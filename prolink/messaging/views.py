from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.db.models import Q, Count, Max, Prefetch
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Conversation, Message
from users.models import CustomUser
from requests.models import Request


@login_required
def inbox(request):
    """
    Display all conversations for the logged-in user with Facebook-style split view
    Optimized with database annotations to avoid N+1 queries
    """
    user = request.user
    
    # Optimized query with annotations to avoid N+1 queries
    conversations = Conversation.objects.filter(
        Q(client=user) | Q(professional=user),
        is_active=True
    ).select_related('client', 'professional', 'request').annotate(
        # Annotate unread count using aggregation
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=user)),
    ).prefetch_related(
        # Prefetch only the last message for each conversation
        Prefetch(
            'messages',
            queryset=Message.objects.select_related('sender').order_by('-created_at')[:1],
            to_attr='last_message_list'
        )
    ).order_by('-updated_at')
    
    # Format timestamps and build conversation list
    now = timezone.now()
    now_local = timezone.localtime(now)
    conversation_list = []
    
    for conv in conversations:
        # Determine the other party
        other_party = conv.professional if user == conv.client else conv.client
        
        # Get last message from prefetched list
        last_message = conv.last_message_list[0] if conv.last_message_list else None
        
        # Format conversation timestamp
        conv_time = timezone.localtime(conv.updated_at)
        if conv_time.date() == now_local.date():
            formatted_conv_time = conv_time.strftime('%I:%M %p').lstrip('0')
        elif (now_local.date() - conv_time.date()).days == 1:
            formatted_conv_time = "Yesterday"
        elif (now_local.date() - conv_time.date()).days < 7:
            formatted_conv_time = conv_time.strftime('%A')
        else:
            formatted_conv_time = conv_time.strftime('%b %d')
        
        conversation_list.append({
            'id': conv.id,
            'request_title': conv.request.title,
            'other_party': other_party,
            'last_message': last_message,
            'unread_count': conv.unread_count or 0,
            'updated_at': conv.updated_at,
            'formatted_updated_at': formatted_conv_time,
        })
    
    # Check if a conversation is selected (for split view)
    selected_conversation = None
    selected_messages = None
    selected_other_party = None
    selected_last_message_id = 0
    
    conversation_id = request.GET.get('conversation_id')
    if conversation_id:
        try:
            selected_conv = Conversation.objects.select_related('client', 'professional', 'request').get(
                id=conversation_id,
                is_active=True
            )
            # Check if user has access
            if user == selected_conv.client or user == selected_conv.professional:
                selected_conversation = selected_conv
                # Mark messages as read
                Message.objects.filter(
                    conversation=selected_conv,
                    is_read=False
                ).exclude(sender=user).update(is_read=True)
                # Get messages with pagination - only load recent messages initially
                messages_queryset = selected_conv.messages.select_related('sender').order_by('-created_at')[:50]
                messages_queryset = list(reversed(messages_queryset))  # Reverse to show oldest first
                selected_last_message_id = messages_queryset[-1].id if messages_queryset else 0
                
                # Format message timestamps
                selected_messages = []
                for msg in messages_queryset:
                    msg_time = timezone.localtime(msg.created_at)
                    # Smart timestamp formatting
                    if msg_time.date() == now_local.date():
                        formatted_msg_time = msg_time.strftime('%I:%M %p').lstrip('0')
                    elif (now_local.date() - msg_time.date()).days == 1:
                        formatted_msg_time = f"Yesterday {msg_time.strftime('%I:%M %p').lstrip('0')}"
                    elif (now_local.date() - msg_time.date()).days < 7:
                        formatted_msg_time = f"{msg_time.strftime('%A')} {msg_time.strftime('%I:%M %p').lstrip('0')}"
                    else:
                        formatted_msg_time = msg_time.strftime('%b %d, %I:%M %p').lstrip('0')
                    
                    # Create message dict with formatted time
                    msg_dict = {
                        'id': msg.id,
                        'sender': msg.sender,
                        'content': msg.content,
                        'created_at': msg.created_at,
                        'formatted_time': formatted_msg_time,
                    }
                    selected_messages.append(msg_dict)
                
                # Get other party
                selected_other_party = selected_conv.professional if user == selected_conv.client else selected_conv.client
        except Conversation.DoesNotExist:
            pass
    
    context = {
        'conversations': conversation_list,
        'user': user,
        'selected_conversation': selected_conversation,
        'selected_messages': selected_messages,
        'selected_other_party': selected_other_party,
        'selected_last_message_id': selected_last_message_id,
    }
    
    return render(request, 'messaging/inbox.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """
    Redirect to inbox with selected conversation (for backward compatibility)
    """
    user = request.user
    
    # Get conversation and verify access
    conversation = get_object_or_404(
        Conversation.objects.select_related('client', 'professional', 'request'),
        id=conversation_id
    )
    
    # Check if user has access to this conversation
    if user != conversation.client and user != conversation.professional:
        django_messages.error(request, "You don't have permission to view this conversation.")
        return redirect('messaging:inbox')
    
    # Redirect to inbox with conversation_id parameter
    from django.urls import reverse
    inbox_url = reverse('messaging:inbox')
    return redirect(f'{inbox_url}?conversation_id={conversation_id}')


@login_required
@require_POST
def send_message(request, conversation_id):
    """
    AJAX endpoint to send a message
    """
    user = request.user
    
    # Get conversation and verify access
    try:
        conversation = Conversation.objects.select_related('client', 'professional').get(id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conversation not found'}, status=404)
    
    # Check if user has access
    if user != conversation.client and user != conversation.professional:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    # Get message content
    content = request.POST.get('content', '').strip()
    
    # Validate content
    if not content:
        return JsonResponse({'success': False, 'error': 'Message cannot be empty'}, status=400)
    
    if len(content) > 1000:
        return JsonResponse({'success': False, 'error': 'Message is too long (max 1000 characters)'}, status=400)
    
    # Create message
    message = Message.objects.create(
        conversation=conversation,
        sender=user,
        content=content
    )
    
    # Update conversation timestamp
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=['updated_at'])
    
    # Notify the recipient of the new message
    recipient = conversation.client if user == conversation.professional else conversation.professional
    from analytics.models import Notification
    from django.urls import reverse
    
    try:
        conversation_url = reverse('messaging:conversation', args=[conversation_id])
    except:
        conversation_url = f'/messages/{conversation_id}/'
    
    Notification.create_notification(
        user=recipient,
        notification_type='message_received',
        title='New Message',
        message=f'You have a new message from {user.get_full_name()} in "{conversation.request.title}".',
        request=conversation.request,
        related_user=user,
        link_url=conversation_url
    )
    
    # Format timestamp - convert to local timezone and format smartly
    now = timezone.now()
    msg_time = timezone.localtime(message.created_at)
    now_local = timezone.localtime(now)
    
    # Smart timestamp formatting: time only for today, date+time for older
    if msg_time.date() == now_local.date():
        # Today: show only time
        formatted_time = msg_time.strftime('%I:%M %p').lstrip('0')
    elif (now_local.date() - msg_time.date()).days == 1:
        # Yesterday
        formatted_time = f"Yesterday {msg_time.strftime('%I:%M %p').lstrip('0')}"
    elif (now_local.date() - msg_time.date()).days < 7:
        # This week: show day name and time
        formatted_time = f"{msg_time.strftime('%A')} {msg_time.strftime('%I:%M %p').lstrip('0')}"
    else:
        # Older: show date and time
        formatted_time = msg_time.strftime('%b %d, %I:%M %p').lstrip('0')
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender_email': message.sender.email,
            'sender_name': message.sender.get_full_name(),
            'created_at': formatted_time,
            'is_own_message': True
        }
    })


@login_required
def get_unread_count(request):
    """
    AJAX endpoint to get unread message count
    Optimized with database aggregation
    """
    user = request.user
    
    # Count total unread messages using database aggregation (single query)
    total_unread = Message.objects.filter(
        conversation__in=Conversation.objects.filter(
            Q(client=user) | Q(professional=user),
            is_active=True
        ),
        is_read=False
    ).exclude(sender=user).count()
    
    return JsonResponse({
        'unread_count': total_unread
    })


@login_required
def get_new_messages(request, conversation_id):
    """
    AJAX endpoint to get new messages since a specific message ID
    """
    user = request.user
    last_message_id = request.GET.get('last_message_id', 0)
    
    try:
        conversation = Conversation.objects.select_related('client', 'professional').get(id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conversation not found'}, status=404)
    
    # Check if user has access
    if user != conversation.client and user != conversation.professional:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    # Get new messages - limit to 50 to avoid large responses
    # First, mark messages as read (before slicing)
    Message.objects.filter(
        conversation=conversation,
        id__gt=last_message_id
    ).exclude(sender=user).update(is_read=True)
    
    # Then get the messages for response (with slice)
    new_messages = Message.objects.filter(
        conversation=conversation,
        id__gt=last_message_id
    ).select_related('sender').order_by('created_at')[:50]
    
    # Format timestamps - convert to local timezone and format smartly
    now = timezone.now()
    now_local = timezone.localtime(now)
    
    messages_data = []
    for msg in new_messages:
        msg_time = timezone.localtime(msg.created_at)
        
        # Smart timestamp formatting: time only for today, date+time for older
        if msg_time.date() == now_local.date():
            # Today: show only time
            formatted_time = msg_time.strftime('%I:%M %p').lstrip('0')
        elif (now_local.date() - msg_time.date()).days == 1:
            # Yesterday
            formatted_time = f"Yesterday {msg_time.strftime('%I:%M %p').lstrip('0')}"
        elif (now_local.date() - msg_time.date()).days < 7:
            # This week: show day name and time
            formatted_time = f"{msg_time.strftime('%A')} {msg_time.strftime('%I:%M %p').lstrip('0')}"
        else:
            # Older: show date and time
            formatted_time = msg_time.strftime('%b %d, %I:%M %p').lstrip('0')
        
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender_email': msg.sender.email,
            'sender_name': msg.sender.get_full_name(),
            'created_at': formatted_time,
            'is_own_message': msg.sender == user
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data
    })

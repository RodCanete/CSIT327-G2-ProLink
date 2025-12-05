from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.db.models import Q, Count, Max
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Conversation, Message
from users.models import CustomUser
from requests.models import Request


@login_required
def inbox(request):
    """
    Display all conversations for the logged-in user with Facebook-style split view
    """
    user = request.user
    
    # Get all conversations where user is either client or professional
    conversations = Conversation.objects.filter(
        Q(client=user) | Q(professional=user),
        is_active=True
    ).select_related('client', 'professional', 'request').prefetch_related('messages')
    
    # Annotate with unread count and last message time
    conversation_list = []
    for conv in conversations:
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(user)
        
        # Determine the other party
        other_party = conv.professional if user == conv.client else conv.client
        
        conversation_list.append({
            'id': conv.id,
            'request_title': conv.request.title,
            'other_party': other_party,
            'last_message': last_message,
            'unread_count': unread_count,
            'updated_at': conv.updated_at,
        })
    
    # Sort by most recent activity
    conversation_list.sort(key=lambda x: x['updated_at'], reverse=True)
    
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
                # Get messages
                selected_messages = selected_conv.messages.select_related('sender').all()
                selected_last_message_id = selected_messages.last().id if selected_messages.exists() else 0
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
    return redirect('messaging:inbox?conversation_id=' + str(conversation_id))


@login_required
@require_POST
def send_message(request, conversation_id):
    """
    AJAX endpoint to send a message
    """
    user = request.user
    
    # Get conversation and verify access
    try:
        conversation = Conversation.objects.get(id=conversation_id)
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
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender_email': message.sender.email,
            'sender_name': message.sender.get_full_name(),
            'created_at': message.created_at.strftime('%b %d, %Y at %I:%M %p'),
            'is_own_message': True
        }
    })


@login_required
def get_unread_count(request):
    """
    AJAX endpoint to get unread message count
    """
    user = request.user
    
    # Get all conversations where user is either client or professional
    conversations = Conversation.objects.filter(
        Q(client=user) | Q(professional=user),
        is_active=True
    )
    
    # Count total unread messages
    total_unread = 0
    for conv in conversations:
        total_unread += conv.get_unread_count(user)
    
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
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conversation not found'}, status=404)
    
    # Check if user has access
    if user != conversation.client and user != conversation.professional:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    # Get new messages
    new_messages = Message.objects.filter(
        conversation=conversation,
        id__gt=last_message_id
    ).select_related('sender').order_by('created_at')
    
    # Mark new messages as read if they're not from current user
    new_messages.exclude(sender=user).update(is_read=True)
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender_email': msg.sender.email,
        'sender_name': msg.sender.get_full_name(),
        'created_at': msg.created_at.strftime('%b %d, %Y at %I:%M %p'),
        'is_own_message': msg.sender == user
    } for msg in new_messages]
    
    return JsonResponse({
        'success': True,
        'messages': messages_data
    })

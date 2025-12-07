from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.db.models import Q
from .models import Notification


@login_required
def get_notification_count(request):
    """Get unread notification count for the current user"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})


@login_required
def get_notifications(request):
    """Get list of notifications for the current user"""
    limit = int(request.GET.get('limit', 20))
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    
    notifications = Notification.objects.filter(user=request.user)
    
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.select_related('request', 'related_user')[:limit]
    
    notification_list = []
    now = timezone.now()
    
    for notif in notifications:
        # Calculate time ago
        time_diff = now - notif.created_at
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds >= 3600:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif time_diff.seconds >= 60:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            time_ago = "Just now"
        
        # Get icon based on notification type
        icon_map = {
            'request_created': 'fa-bell',
            'request_accepted': 'fa-check-circle',
            'request_updated': 'fa-edit',
            'payment_received': 'fa-money-bill-wave',
            'work_submitted': 'fa-file-upload',
            'revision_requested': 'fa-redo',
            'work_approved': 'fa-check-double',
            'dispute_opened': 'fa-exclamation-triangle',
            'dispute_resolved': 'fa-gavel',
            'message_received': 'fa-envelope',
            'review_received': 'fa-star',
            'price_proposed': 'fa-tag',
            'price_accepted': 'fa-handshake',
            'price_rejected': 'fa-times-circle',
        }
        icon = icon_map.get(notif.notification_type, 'fa-bell')
        
        # Get related user name if available
        from_user = None
        if notif.related_user:
            from_user = notif.related_user.get_full_name() or notif.related_user.username
        
        # Get request title if available
        request_title = None
        if notif.request:
            request_title = notif.request.title
        
        notification_list.append({
            'id': notif.id,
            'type': notif.notification_type,
            'title': notif.title,
            'message': notif.message,
            'is_read': notif.is_read,
            'time_ago': time_ago,
            'icon': icon,
            'link_url': notif.link_url,
            'created_at': notif.created_at.isoformat(),
            'from_user': from_user,
            'request_title': request_title,
        })
    
    return JsonResponse({'notifications': notification_list})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    updated = Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    return JsonResponse({'success': True, 'updated_count': updated})

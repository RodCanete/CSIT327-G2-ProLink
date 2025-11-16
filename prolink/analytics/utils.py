"""
Utility functions for analytics and dashboard metrics
"""
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Review, ActivityLog
from requests.models import Request
from users.models import CustomUser, ProfessionalProfile


def get_client_dashboard_metrics(user):
    """
    Calculate dashboard metrics for client users
    Returns a dictionary with all necessary metrics
    """
    # Get user's requests
    user_requests = Request.objects.filter(
        client=user.email if hasattr(user, 'email') else user.username
    )
    
    # Active requests (pending + in_progress)
    active_requests = user_requests.filter(
        Q(status='pending') | Q(status='in_progress')
    ).count()
    
    # In progress count
    in_progress_requests = user_requests.filter(status='in_progress').count()
    
    # Completed validations
    completed_validations = user_requests.filter(status='completed').count()
    
    # Reviews given
    reviews_given = Review.objects.filter(
        reviewer=user,
        is_professional_review=False
    ).count()
    
    # Average rating given
    avg_rating_given = Review.objects.filter(
        reviewer=user,
        is_professional_review=False
    ).aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Calculate trends (compare to last month)
    last_month = timezone.now() - timedelta(days=30)
    
    active_requests_trend = user_requests.filter(
        Q(status='pending') | Q(status='in_progress'),
        created_at__gte=last_month
    ).count()
    
    completed_this_month = user_requests.filter(
        status='completed',
        completed_at__gte=last_month
    ).count()
    
    reviews_this_month = Review.objects.filter(
        reviewer=user,
        is_professional_review=False,
        created_at__gte=last_month
    ).count()
    
    return {
        'active_requests': active_requests,
        'in_progress_requests': in_progress_requests,
        'completed_validations': completed_validations,
        'reviews_given': reviews_given,
        'avg_rating_given': round(avg_rating_given, 1),
        'trends': {
            'active_requests': active_requests_trend,
            'completed_this_month': completed_this_month,
            'reviews_this_month': reviews_this_month,
        }
    }


def get_recent_activities(user, limit=10):
    """
    Get recent activities for a user
    Returns QuerySet of ActivityLog objects
    """
    return ActivityLog.objects.filter(user=user)[:limit]


def get_active_requests_tracking(user, limit=5):
    """
    Get active requests with progress tracking
    Returns list of requests with calculated progress
    """
    user_email = user.email if hasattr(user, 'email') else user.username
    
    requests = Request.objects.filter(
        client=user_email
    ).exclude(
        status__in=['cancelled']
    ).select_related('transaction', 'conversation').order_by('-updated_at')[:limit]
    
    tracking_data = []
    for req in requests:
        # Calculate progress based on status
        if req.status == 'completed':
            progress = 100
        elif req.status == 'in_progress':
            # Calculate based on time elapsed
            if req.timeline_days > 0:
                days_elapsed = (timezone.now() - req.created_at).days
                progress = min(int((days_elapsed / req.timeline_days) * 100), 95)
            else:
                progress = 50
        elif req.status == 'pending':
            progress = 10
        else:
            progress = 0
        
        # Get professional name
        professional_name = req.professional if req.professional else "Awaiting Assignment"
        
        tracking_data.append({
            'request': req,
            'progress': progress,
            'professional_name': professional_name,
            'status_display': req.get_status_display()
        })
    
    return tracking_data


def get_recommended_professionals(user, limit=3):
    """
    Get recommended professionals based on:
    1. High ratings
    2. Related to user's past request categories (if applicable)
    3. Available professionals
    """
    # Get user's request history to find relevant specializations
    user_email = user.email if hasattr(user, 'email') else user.username
    user_requests = Request.objects.filter(client=user_email)
    
    # Get all professionals with profiles
    professionals = ProfessionalProfile.objects.filter(
        user__user_role='professional',
        is_available=True
    ).select_related('user').prefetch_related('specializations')
    
    # Filter by minimum rating and sort by rating and reviews
    professionals = professionals.filter(
        average_rating__gte=4.0,
        total_reviews__gte=1
    ).order_by('-average_rating', '-total_reviews')[:limit * 2]
    
    # If user has request history, prioritize related specializations
    # For now, just return top-rated professionals
    
    return list(professionals[:limit])


def create_activity_log(user, activity_type, description, request=None, related_user=None, review=None):
    """
    Wrapper function to create activity logs
    """
    return ActivityLog.log_activity(
        user=user,
        activity_type=activity_type,
        description=description,
        request=request,
        related_user=related_user,
        review=review
    )


def format_activity_for_display(activity):
    """
    Format activity log for display in dashboard
    Returns dict with formatted activity data
    """
    # Determine icon and color based on activity type
    icon_map = {
        'request_completed': ('fas fa-check-circle', 'success'),
        'request_in_progress': ('fas fa-clock', 'warning'),
        'request_created': ('fas fa-clipboard-list', 'info'),
        'professional_connected': ('fas fa-user-plus', 'info'),
        'review_given': ('fas fa-star', 'success'),
        'review_received': ('fas fa-star', 'success'),
        'message_sent': ('fas fa-envelope', 'info'),
        'message_received': ('fas fa-envelope-open', 'info'),
    }
    
    icon, color = icon_map.get(activity.activity_type, ('fas fa-circle', 'info'))
    
    # Calculate time ago
    time_diff = timezone.now() - activity.created_at
    
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
    
    return {
        'description': activity.description,
        'icon': icon,
        'color': color,
        'time_ago': time_ago,
        'created_at': activity.created_at
    }

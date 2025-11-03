"""
Signal handlers for automatic activity logging
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from requests.models import Request
from .models import ActivityLog, Review


@receiver(post_save, sender=Request)
def log_request_activity(sender, instance, created, **kwargs):
    """
    Automatically log activity when a request is created or updated
    """
    from users.models import CustomUser
    
    # Get the client user
    try:
        client = CustomUser.objects.get(email=instance.client)
    except CustomUser.DoesNotExist:
        return
    
    if created:
        # Request was just created
        ActivityLog.log_activity(
            user=client,
            activity_type='request_created',
            description=f'<strong>Request created:</strong> "{instance.title}"',
            request=instance
        )
    else:
        # Request was updated - check status changes
        if instance.status == 'in_progress':
            # Get professional if exists
            professional_name = instance.professional or "Professional"
            ActivityLog.log_activity(
                user=client,
                activity_type='request_in_progress',
                description=f'<strong>Request in progress:</strong> "{instance.title}" by {professional_name}',
                request=instance
            )
        elif instance.status == 'completed':
            professional_name = instance.professional or "Professional"
            ActivityLog.log_activity(
                user=client,
                activity_type='request_completed',
                description=f'<strong>Validation completed:</strong> "{instance.title}" by {professional_name}',
                request=instance
            )
        elif instance.status == 'cancelled':
            ActivityLog.log_activity(
                user=client,
                activity_type='request_cancelled',
                description=f'<strong>Request cancelled:</strong> "{instance.title}"',
                request=instance
            )


@receiver(post_save, sender=Review)
def log_review_activity(sender, instance, created, **kwargs):
    """
    Automatically log activity when a review is given
    """
    if created:
        # Review was just created
        ActivityLog.log_activity(
            user=instance.reviewer,
            activity_type='review_given',
            description=f'<strong>Left {instance.rating}-star review</strong> for {instance.reviewee.get_full_name() or instance.reviewee.username}',
            review=instance,
            related_user=instance.reviewee
        )
        
        # Also log for the reviewee
        if instance.is_visible_to_client:
            ActivityLog.log_activity(
                user=instance.reviewee,
                activity_type='review_received',
                description=f'<strong>Received {instance.rating}-star review</strong> from {instance.reviewer.get_full_name() or instance.reviewer.username}',
                review=instance,
                related_user=instance.reviewer
            )

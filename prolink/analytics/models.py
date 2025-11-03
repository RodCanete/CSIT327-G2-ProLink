from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser, ProfessionalProfile
from requests.models import Request


class Review(models.Model):
    """
    Reviews for professionals from clients and vice versa
    """
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_given')
    reviewee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_received')
    
    # Review content
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    
    # Review metadata
    is_professional_review = models.BooleanField(
        default=False,
        help_text="True if professional reviewing client, False if client reviewing professional"
    )
    is_visible_to_client = models.BooleanField(
        default=True,
        help_text="Professional reviews of clients are hidden from clients"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('request', 'reviewer', 'reviewee')
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
    
    def __str__(self):
        return f"{self.reviewer.username} → {self.reviewee.username} ({self.rating}★)"
    
    def save(self, *args, **kwargs):
        # Set visibility based on review type
        if self.is_professional_review:
            self.is_visible_to_client = False
        else:
            self.is_visible_to_client = True
        
        super().save(*args, **kwargs)
        
        # Update professional's average rating if reviewing a professional
        if not self.is_professional_review and hasattr(self.reviewee, 'professional_profile'):
            self.update_professional_rating()
    
    def update_professional_rating(self):
        """Update the professional's average rating and total reviews"""
        professional = self.reviewee.professional_profile
        reviews = Review.objects.filter(
            reviewee=self.reviewee,
            is_professional_review=False
        )
        
        professional.total_reviews = reviews.count()
        if professional.total_reviews > 0:
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            professional.average_rating = round(avg_rating, 2)
        else:
            professional.average_rating = 0.00
        
        professional.save()


class ActivityLog(models.Model):
    """
    Real-time activity logging for dashboard feeds
    """
    ACTIVITY_TYPES = (
        ('request_created', 'Request Created'),
        ('request_updated', 'Request Updated'),
        ('request_in_progress', 'Request In Progress'),
        ('request_completed', 'Request Completed'),
        ('request_cancelled', 'Request Cancelled'),
        ('professional_connected', 'Professional Connected'),
        ('review_given', 'Review Given'),
        ('review_received', 'Review Received'),
        ('message_sent', 'Message Sent'),
        ('message_received', 'Message Received'),
        ('profile_viewed', 'Profile Viewed'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    
    # Related objects
    request = models.ForeignKey(Request, on_delete=models.CASCADE, null=True, blank=True)
    related_user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='related_activities'
    )
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True)
    
    # Activity details
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def log_activity(cls, user, activity_type, description, request=None, related_user=None, review=None, metadata=None):
        """
        Helper method to create activity logs
        """
        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            request=request,
            related_user=related_user,
            review=review,
            metadata=metadata or {}
        )


class Transaction(models.Model):
    """
    Payment transactions - placeholder for future implementation
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='transactions')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments_made')
    professional = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments_received')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"${self.amount} - {self.client.username} → {self.professional.username} - {self.get_status_display()}"

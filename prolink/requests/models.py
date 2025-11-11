from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Request(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('declined', 'Declined'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    client = models.CharField(max_length=100)  # Client/Student email
    professional = models.CharField(max_length=100, blank=True)  # Professional email
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    timeline_days = models.IntegerField(default=7)  # Expected completion in days
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # File attachments (stored as JSON string for simplicity)
    attached_files = models.TextField(blank=True)  # JSON string of file URLs
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

class RequestMessage(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='messages')
    sender_email = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_from_professional = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message for {self.request.title} - {self.sender_email}"
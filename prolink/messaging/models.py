from django.db import models
from users.models import CustomUser
from requests.models import Request


class Conversation(models.Model):
    """
    Represents a conversation between a client and professional
    Created when professional accepts a request
    """
    request = models.OneToOneField(Request, on_delete=models.CASCADE, related_name='conversation')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='client_conversations')
    professional = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='professional_conversations')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['client', 'professional']),
            models.Index(fields=['-updated_at']),
        ]
    
    def __str__(self):
        return f"Conversation: {self.client.email} & {self.professional.email} - {self.request.title}"
    
    def get_unread_count(self, user):
        """Get unread message count for a specific user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    def get_last_message(self):
        """Get the last message in the conversation"""
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """
    Individual message in a conversation
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(max_length=1000)  # 1000 character limit
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['is_read']),
            models.Index(fields=['conversation', 'is_read', 'sender']),  # Optimize unread count queries
        ]
    
    def __str__(self):
        return f"Message from {self.sender.email} at {self.created_at}"
    
    def mark_as_read(self):
        """Mark this message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

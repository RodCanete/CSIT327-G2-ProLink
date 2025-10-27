from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    # Fix group conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_groups',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_permissions',
        related_query_name='user',
    )

    # 🔑 New field to link with Supabase users
    supabase_id = models.UUIDField(unique=True, null=True, blank=True, editable=False)

    USER_TYPE_CHOICES = (
        ('client', 'Client'),
        ('professional', 'Professional'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='client')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/images/default_profile.png'

    def __str__(self):
        return f"{self.username} ({self.user_type})"

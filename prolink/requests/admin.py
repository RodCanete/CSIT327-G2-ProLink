from django.contrib import admin
from .models import Request, RequestMessage

# Register your models here.

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'professional', 'status', 'price', 'created_at']
    list_filter = ['status', 'created_at', 'timeline_days']
    search_fields = ['title', 'client', 'professional', 'description']
    list_editable = ['status', 'price']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'client', 'professional')
        }),
        ('Status & Pricing', {
            'fields': ('status', 'price', 'timeline_days')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
        ('Files', {
            'fields': ('attached_files',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']

@admin.register(RequestMessage)
class RequestMessageAdmin(admin.ModelAdmin):
    list_display = ['request', 'sender_email', 'is_from_professional', 'created_at']
    list_filter = ['is_from_professional', 'created_at']
    search_fields = ['request__title', 'sender_email', 'message']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('request', 'sender_email', 'is_from_professional')
        }),
        ('Content', {
            'fields': ('message',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ['created_at']

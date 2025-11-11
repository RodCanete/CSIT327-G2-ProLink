from django.contrib import admin
from .models import Review, ActivityLog


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewee', 'rating', 'is_professional_review', 'created_at')
    list_filter = ('rating', 'is_professional_review', 'created_at')
    search_fields = ('reviewer__username', 'reviewer__email', 'reviewee__username', 'reviewee__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Details', {
            'fields': ('request', 'reviewer', 'reviewee', 'rating', 'comment')
        }),
        ('Metadata', {
            'fields': ('is_professional_review', 'is_visible_to_client', 'created_at', 'updated_at')
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description_short', 'created_at', 'is_read')
    list_filter = ('activity_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'description')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'


# Transaction and Dispute admin moved to transactions app


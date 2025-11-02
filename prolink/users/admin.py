from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ProfessionalProfile, Specialization, SavedProfessional


# Custom User Admin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_role', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('user_role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    
    fieldsets = UserAdmin.fieldsets + (
        ('User Role', {'fields': ('user_role',)}),
        ('Contact Info', {'fields': ('phone_number',)}),
        ('Profile', {'fields': ('profile_picture', 'bio', 'date_of_birth')}),
        ('Student/Worker Info', {
            'fields': ('school_name', 'major', 'year_level', 'graduation_year', 'company_name', 'job_title'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('User Role', {'fields': ('user_role',)}),
    )


# Specialization Admin
@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)


# Professional Profile Admin
@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_level', 'hourly_rate', 'average_rating', 'total_reviews', 'is_available', 'is_verified')
    list_filter = ('experience_level', 'is_available', 'is_verified', 'is_featured')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    filter_horizontal = ('specializations',)
    readonly_fields = ('total_consultations', 'completed_consultations', 'average_rating', 'total_reviews', 'profile_views', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Professional Details', {
            'fields': ('specializations', 'experience_level', 'years_of_experience')
        }),
        ('Credentials', {
            'fields': ('certifications', 'education', 'languages')
        }),
        ('Pricing & Availability', {
            'fields': ('hourly_rate', 'consultation_fee', 'is_available', 'timezone')
        }),
        ('Statistics (Read-only)', {
            'fields': ('total_consultations', 'completed_consultations', 'average_rating', 'total_reviews', 'profile_views'),
            'classes': ('collapse',)
        }),
        ('Portfolio & Links', {
            'fields': ('portfolio_url', 'linkedin_url', 'website_url')
        }),
        ('Profile Status', {
            'fields': ('is_verified', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Saved Professional Admin
@admin.register(SavedProfessional)
class SavedProfessionalAdmin(admin.ModelAdmin):
    list_display = ('user', 'professional', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__username', 'professional__user__username')
    readonly_fields = ('saved_at',)

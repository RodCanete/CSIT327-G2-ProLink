from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

# Custom User Model
class CustomUser(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Supports different user roles: client, student, worker, professional
    """
    USER_ROLES = (
        ('client', 'Client'),
        ('student', 'Student'),
        ('worker', 'Worker'),
        ('professional', 'Professional'),
    )
    
    user_role = models.CharField(max_length=20, choices=USER_ROLES, default='client')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Student/Worker specific fields
    school_name = models.CharField(max_length=200, blank=True, null=True)
    major = models.CharField(max_length=200, blank=True, null=True)
    year_level = models.CharField(max_length=50, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    job_title = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_role_display()})"
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


# Specialization Categories
class Specialization(models.Model):
    """
    Predefined specialization categories for professionals
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Specialization'
        verbose_name_plural = 'Specializations'


# Professional Profile
class ProfessionalProfile(models.Model):
    """
    Extended profile for professional users.
    Linked to CustomUser with OneToOne relationship.
    """
    EXPERIENCE_LEVELS = (
        ('entry', 'Entry Level (0-2 years)'),
        ('intermediate', 'Intermediate (3-5 years)'),
        ('experienced', 'Experienced (6-10 years)'),
        ('expert', 'Expert (10+ years)'),
    )
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='professional_profile')
    
    # Professional Details
    specializations = models.ManyToManyField(Specialization, related_name='professionals')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='entry')
    years_of_experience = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    
    # Credentials
    certifications = models.TextField(blank=True, help_text="List certifications, one per line")
    education = models.TextField(blank=True, help_text="Educational background")
    languages = models.CharField(max_length=200, blank=True, help_text="Languages spoken (comma separated)")
    
    # Pricing & Availability
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    is_available = models.BooleanField(default=True)
    timezone = models.CharField(max_length=50, blank=True)
    
    # Social Proof & Statistics
    total_consultations = models.IntegerField(default=0)
    completed_consultations = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, 
                                        validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.IntegerField(default=0)
    
    # Portfolio & Links
    portfolio_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    
    # Profile Status
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    profile_views = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Professional Profile"
    
    @property
    def response_rate(self):
        """Calculate response rate percentage"""
        if self.total_consultations == 0:
            return 0
        return round((self.completed_consultations / self.total_consultations) * 100, 2)
    
    class Meta:
        verbose_name = 'Professional Profile'
        verbose_name_plural = 'Professional Profiles'


# Saved Professionals (Bookmarks)
class SavedProfessional(models.Model):
    """
    Allows clients to save/bookmark professionals for later
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saved_professionals')
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='saved_by')
    notes = models.TextField(blank=True, help_text="Private notes about this professional")
    saved_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} saved {self.professional.user.username}"
    
    class Meta:
        unique_together = ('user', 'professional')
        ordering = ['-saved_at']
        verbose_name = 'Saved Professional'
        verbose_name_plural = 'Saved Professionals'

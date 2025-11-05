
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import json
from requests.models import Request as ServiceRequest
from analytics.utils import (
    get_client_dashboard_metrics,
    get_recent_activities,
    get_active_requests_tracking,
    get_recommended_professionals,
    format_activity_for_display
)

def landing(request):
	return render(request, "landing.html")

@login_required
def dashboard(request):
    """
    Dashboard view - routes to appropriate dashboard based on user role
    """
    user = request.user
    user_role = user.user_role if hasattr(user, 'user_role') else 'client'
    
    # Use first name for display, falling back to username
    display_name = user.get_full_name() or user.username
    
    # Define the base context dictionary
    context = {
        "display_name": display_name, 
        "user_email": user.email,
        "user_role": user_role,
        "user": user
    }
    
    # Route to appropriate dashboard based on role
    if user_role == 'professional':
        return render(request, "dashboard_professional.html", context)
    else:  # student, worker, or client
        # Get dashboard metrics
        metrics = get_client_dashboard_metrics(user)
        
        # Get recent activities
        activities = get_recent_activities(user, limit=4)
        formatted_activities = [format_activity_for_display(activity) for activity in activities]
        
        # Get active requests tracking
        active_requests_data = get_active_requests_tracking(user, limit=3)
        
        # Get recommended professionals
        recommended_professionals = get_recommended_professionals(user, limit=3)
        
        # Add to context
        context.update({
            'metrics': metrics,
            'recent_activities': formatted_activities,
            'active_requests_tracking': active_requests_data,
            'recommended_professionals': recommended_professionals,
        })
        
        return render(request, "dashboard_client.html", context)

def logout(request):
    """
    Logout view - logs out user and redirects to landing page
    """
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("landing")

def login(request):
    """
    Django-based login view
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    
    error = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        # Django auth uses username, but we want email login
        # Try to authenticate with email as username
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, "Login successful!")
            
            # Redirect to next page or dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            error = "Invalid email or password."
            
    return render(request, "users/login.html", {"error": error})

def signup(request):
    """
    Django-based signup view
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    
    from .models import CustomUser, ProfessionalProfile, Specialization
    
    error = None
    if request.method == "POST":
        # Get form data
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number", "")
        date_of_birth = request.POST.get("date_of_birth", "")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        role = request.POST.get("role", "client")
        terms = request.POST.get("terms")
        
        # Get role-specific data
        profession = request.POST.get("profession", "")
        experience = request.POST.get("experience", "")
        other_profession = request.POST.get("other_profession", "")
        
        # Student-specific fields
        school_name = request.POST.get("school_name", "")
        major = request.POST.get("major", "")
        year_level = request.POST.get("year_level", "")
        graduation_year = request.POST.get("graduation_year", "")
        
        # Worker-specific fields
        company_name = request.POST.get("company_name", "")
        job_title = request.POST.get("job_title", "")
        
        # Basic validation
        if not all([first_name, last_name, email, password1, password2, terms]):
            error = "Please fill in all required fields."
        elif password1 != password2:
            error = "Passwords do not match."
        elif len(password1) < 8:
            error = "Password must be at least 8 characters long."
        elif CustomUser.objects.filter(email=email).exists():
            error = "An account with this email already exists."
        else:
            # Create user account with Django
            try:
                # Create the user
                user = CustomUser.objects.create_user(
                    username=email,  # Use email as username
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    user_role=role,
                    phone_number=phone_number if phone_number else None,
                    date_of_birth=date_of_birth if date_of_birth else None
                )
                
                # Build bio from role-specific data
                bio_parts = []
                if role == "professional":
                    if profession:
                        prof_display = other_profession if profession == "other" else profession
                        bio_parts.append(f"Professional in {prof_display}")
                    if experience:
                        bio_parts.append(f"{experience} level experience")
                elif role == "student":
                    # Save student-specific fields
                    if school_name:
                        user.school_name = school_name
                        bio_parts.append(f"Student at {school_name}")
                    if major:
                        user.major = major
                        bio_parts.append(f"Major: {major}")
                    if year_level:
                        user.year_level = year_level
                        bio_parts.append(f"Year {year_level}")
                    if graduation_year:
                        user.graduation_year = int(graduation_year)
                        bio_parts.append(f"Graduating {graduation_year}")
                elif role == "worker":
                    # Save worker-specific fields
                    if company_name:
                        user.company_name = company_name
                        bio_parts.append(f"at {company_name}")
                    if job_title:
                        user.job_title = job_title
                        bio_parts.append(f"{job_title}")
                
                if bio_parts:
                    user.bio = " | ".join(bio_parts)
                    user.save()
                
                # If professional, create professional profile
                if role == "professional":
                    profile = ProfessionalProfile.objects.create(
                        user=user,
                        experience_level='entry' if experience == 'entry' else 
                                       'intermediate' if experience == 'intermediate' else
                                       'experienced' if experience == 'experienced' else
                                       'expert',
                        years_of_experience=0,
                        hourly_rate=50.00,
                        is_available=True
                    )
                    
                    # Add specialization if profession is specified
                    if profession and profession != "other":
                        try:
                            specialization = Specialization.objects.get(name__iexact=profession)
                            profile.specializations.add(specialization)
                        except Specialization.DoesNotExist:
                            pass
                
                # Redirect to registration success page with user info
                messages.success(request, "Account created successfully! Welcome to ProLink.")
                return render(request, "users/registration_success.html", {
                    "name": f"{first_name} {last_name}",
                    "email": email
                })
                    
            except Exception as e:
                error = f"Registration failed: {str(e)}"
    
    from datetime import date
    context = {
        "error": error,
        "today": date.today().isoformat()
    }
    return render(request, "users/signup.html", context)

def terms(request):
    return render(request, 'users/terms.html')

def privacy(request):
    return render(request, 'users/privacy.html')


# ========== PROFESSIONALS VIEWS ==========

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import ProfessionalProfile, Specialization, SavedProfessional, CustomUser


@login_required
def find_professionals(request):
    """
    Main view for browsing and searching professionals
    """
    # Get all active specializations for filter
    specializations = Specialization.objects.filter(is_active=True)
    
    # Start with all available professionals
    professionals = ProfessionalProfile.objects.filter(
        user__is_active=True
    ).select_related('user').prefetch_related('specializations')
    
    # Search by query
    query = request.GET.get('q', '').strip()
    if query:
        professionals = professionals.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__bio__icontains=query) |
            Q(specializations__name__icontains=query) |
            Q(certifications__icontains=query) |
            Q(education__icontains=query)
        ).distinct()
    
    # Filter by specialization
    specialization_id = request.GET.get('specialization')
    if specialization_id:
        professionals = professionals.filter(specializations__id=specialization_id)
    
    # Filter by experience level
    experience = request.GET.get('experience')
    if experience:
        professionals = professionals.filter(experience_level=experience)
    
    # Filter by price range
    min_rate = request.GET.get('min_rate')
    if min_rate:
        try:
            professionals = professionals.filter(hourly_rate__gte=float(min_rate))
        except ValueError:
            pass
    
    max_rate = request.GET.get('max_rate')
    if max_rate:
        try:
            professionals = professionals.filter(hourly_rate__lte=float(max_rate))
        except ValueError:
            pass
    
    # Filter by minimum rating
    min_rating = request.GET.get('min_rating')
    if min_rating:
        try:
            professionals = professionals.filter(average_rating__gte=float(min_rating))
        except ValueError:
            pass
    
    # Filter by availability
    availability = request.GET.get('availability')
    if availability == 'available':
        professionals = professionals.filter(is_available=True)
    
    # Sorting
    sort_by = request.GET.get('sort_by', 'rating')
    if sort_by == 'rating':
        professionals = professionals.order_by('-average_rating', '-total_reviews')
    elif sort_by == 'reviews':
        professionals = professionals.order_by('-total_reviews', '-average_rating')
    elif sort_by == 'price_low':
        professionals = professionals.order_by('hourly_rate')
    elif sort_by == 'price_high':
        professionals = professionals.order_by('-hourly_rate')
    elif sort_by == 'newest':
        professionals = professionals.order_by('-created_at')
    
    # Get saved professionals for current user
    saved_professionals = []
    if request.user.is_authenticated:
        saved_professionals = SavedProfessional.objects.filter(
            user=request.user
        ).values_list('professional_id', flat=True)
    
    # Pagination
    paginator = Paginator(professionals, 12)  # 12 professionals per page
    page_number = request.GET.get('page')
    professionals_page = paginator.get_page(page_number)
    
    context = {
        'professionals': professionals_page,
        'specializations': specializations,
        'saved_professionals': list(saved_professionals),
        'total_count': professionals.count(),
    }
    
    return render(request, 'professionals/professionals_list.html', context)


@login_required
def professional_detail(request, pk):
    """
    Detailed view of a single professional
    """
    professional = get_object_or_404(
        ProfessionalProfile.objects.select_related('user').prefetch_related('specializations'),
        pk=pk
    )
    
    # Increment profile views
    professional.profile_views += 1
    professional.save(update_fields=['profile_views'])
    
    # Check if user has saved this professional
    is_saved = SavedProfessional.objects.filter(
        user=request.user,
        professional=professional
    ).exists()
    
    context = {
        'professional': professional,
        'is_saved': is_saved,
    }
    
    return render(request, 'professionals/professional_detail.html', context)


@login_required
def save_professional(request, pk):
    """
    Save/bookmark a professional (AJAX endpoint)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        professional = ProfessionalProfile.objects.get(pk=pk)
        
        # Create saved professional entry
        SavedProfessional.objects.get_or_create(
            user=request.user,
            professional=professional
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Professional saved successfully'
        })
    
    except ProfessionalProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Professional not found'
        })


@login_required
def unsave_professional(request, pk):
    """
    Unsave/remove bookmark from a professional (AJAX endpoint)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        professional = ProfessionalProfile.objects.get(pk=pk)
        
        # Delete saved professional entry
        SavedProfessional.objects.filter(
            user=request.user,
            professional=professional
        ).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Professional removed from saved list'
        })
    
    except ProfessionalProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Professional not found'
        })


@login_required
def saved_professionals_list(request):
    """
    List of saved professionals for the current user
    """
    saved = SavedProfessional.objects.filter(
        user=request.user
    ).select_related('professional__user').prefetch_related('professional__specializations').order_by('-saved_at')
    
    context = {
        'saved_professionals': saved,
    }
    
    return render(request, 'professionals/saved_professionals.html', context)


@login_required
def user_profile(request):
    """
    Display user profile page with actual database data
    """
    user = request.user
    
    # Get user statistics - using email since Request model uses email for client field
    active_requests = ServiceRequest.objects.filter(client=user.email, status__in=['pending', 'in_progress']).count()
    completed_projects = ServiceRequest.objects.filter(client=user.email, status='completed').count()
    
    # Get connections count (saved professionals)
    connections_count = SavedProfessional.objects.filter(user=user).count()
    
    # Calculate satisfaction rate (placeholder - implement based on your review system)
    satisfaction_rate = 95  # You can calculate this based on actual reviews
    
    context = {
        'user': user,
        'first_name': user.first_name or 'User',
        'last_name': user.last_name or '',
        'display_name': user.get_full_name() or user.username,
        'user_email': user.email,
        'active_requests': active_requests,
        'completed_projects': completed_projects,
        'connections_count': connections_count,
        'satisfaction_rate': satisfaction_rate,
        'member_since': user.date_joined.strftime('%B %Y'),
        'last_login': user.last_login.strftime('%B %d, %Y %I:%M %p') if user.last_login else 'Never',
    }
    
    return render(request, 'users/client_profile.html', context)


@login_required
def user_settings(request):
    """
    Display user settings page
    """
    if request.method == 'POST':
        # Handle form submission
        if 'first_name' in request.POST:
            # Update user profile
            request.user.first_name = request.POST.get('first_name')
            request.user.last_name = request.POST.get('last_name')
            request.user.email = request.POST.get('email')
            request.user.save()
        
        return redirect('user_settings')
    
    return render(request, 'users/settings.html')


@login_required
def transactions(request):
    """
    Display transactions page (coming soon)
    """
    return render(request, 'transactions.html')

@login_required
def edit_profile_picture(request):
    from django.http import JsonResponse
    from django.conf import settings
    from supabase import create_client
    import uuid
    from datetime import datetime
    
    print("🔵 NEW SUPABASE VERSION RUNNING!")
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    if 'profile_picture' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    try:
        file = request.FILES['profile_picture']
        print(f"📁 File received: {file.name}")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            return JsonResponse({'error': 'Invalid file type. Only images allowed.'}, status=400)
        
        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'File too large. Maximum size is 5MB.'}, status=400)
        
        print("☁️ Attempting Supabase upload...")
        
        # Initialize Supabase client with SERVICE_ROLE_KEY to bypass RLS
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        # Generate unique filename
        file_extension = file.name.split('.')[-1] if '.' in file.name else 'jpg'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{request.user.id}_{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = f"profile_pictures/{unique_filename}"
        
        # Read file content
        file_content = file.read()
        
        print(f"📤 Uploading to Supabase: {file_path}")
        
        # Upload to Supabase Storage
        storage_response = supabase.storage.from_('avatars').upload(
            file_path,
            file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_('avatars').get_public_url(file_path)
        
        print(f"✅ Supabase URL: {public_url}")
        
        # Update user's profile_picture field
        request.user.profile_picture = public_url
        request.user.save()
        
        return JsonResponse({
            'success': True,
            'image_url': public_url,
            'message': 'Profile picture updated successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()  # More detailed error logging
        return JsonResponse({
            'error': f'Upload failed: {str(e)}'
        }, status=500)
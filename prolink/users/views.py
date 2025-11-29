
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import json
from decimal import Decimal
from requests.models import Request as ServiceRequest
from users.models import CustomUser
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from datetime import timedelta
from transactions.models import Transaction
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
    # Refresh user from database to get latest profile_picture
    user = request.user
    print(f"🏠 Dashboard - Before refresh: User {user.id}, profile_picture: {user.profile_picture}")
    user.refresh_from_db()
    print(f"🏠 Dashboard - After refresh: User {user.id}, profile_picture: {user.profile_picture}")
    
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
        from transactions.models import Transaction
        from analytics.models import Review
        from django.db.models import Q
        
        # Calculate date ranges for metrics
        today = timezone.now()
        this_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(seconds=1)
        
        # Get all requests for this professional
        professional_requests = ServiceRequest.objects.filter(professional=user.email)
        
        # KPI 1: Total Clients Served (unique clients from completed/accepted requests)
        completed_requests = professional_requests.filter(
            Q(status='completed') | Q(status='awaiting_payment') | Q(status='in_progress') | Q(status='under_review')
        )
        total_clients_served = completed_requests.values('client').distinct().count()
        
        # Clients this month
        clients_this_month = completed_requests.filter(
            created_at__gte=this_month_start
        ).values('client').distinct().count()
        
        # Calculate trend for clients
        clients_last_month = completed_requests.filter(
            created_at__gte=last_month_start,
            created_at__lte=last_month_end
        ).values('client').distinct().count()
        clients_trend = ((clients_this_month - clients_last_month) / clients_last_month * 100) if clients_last_month > 0 else 0
        
        # KPI 2: Active Projects (in_progress requests)
        active_projects = professional_requests.filter(status='in_progress').count()
        pending_requests_count = professional_requests.filter(status='pending').count()
        
        # Active projects trend
        active_projects_last_month = professional_requests.filter(
            status='in_progress',
            created_at__gte=last_month_start,
            created_at__lte=last_month_end
        ).count()
        active_projects_trend = ((active_projects - active_projects_last_month) / active_projects_last_month * 100) if active_projects_last_month > 0 else 0
        
        # KPI 3: Earnings This Month (from released payments)
        this_month_transactions = Transaction.objects.filter(
            professional=user,
            released_at__gte=this_month_start
        )
        earnings_this_month_decimal = this_month_transactions.filter(
            released_at__isnull=False
        ).aggregate(total=Sum('professional_payout'))['total'] or Decimal('0')
        earnings_this_month = float(earnings_this_month_decimal)
        
        # Earnings last month for trend
        last_month_transactions = Transaction.objects.filter(
            professional=user,
            released_at__gte=last_month_start,
            released_at__lte=last_month_end
        )
        earnings_last_month_decimal = last_month_transactions.filter(
            released_at__isnull=False
        ).aggregate(total=Sum('professional_payout'))['total'] or Decimal('0')
        earnings_last_month = float(earnings_last_month_decimal)
        
        # Calculate trend percentage
        if earnings_last_month > 0:
            earnings_trend = ((earnings_this_month - earnings_last_month) / earnings_last_month * 100)
        else:
            earnings_trend = 100 if earnings_this_month > 0 else 0
        
        # Average earning per project this month
        completed_this_month = this_month_transactions.filter(
            released_at__isnull=False
        ).count()
        avg_earning_per_project = (earnings_this_month / completed_this_month) if completed_this_month > 0 else 0
        
        # KPI 4: Average Rating
        reviews_received = Review.objects.filter(
            reviewee=user,
            is_professional_review=False
        )
        avg_rating = reviews_received.aggregate(avg=Avg('rating'))['avg'] or 0
        total_reviews = reviews_received.count()
        
        # Get pending requests for this professional
        pending_requests = professional_requests.filter(
            status='pending'
        ).order_by('-created_at')[:10]
        
        # Attach client user objects to each request
        for req in pending_requests:
            try:
                req.client_user = CustomUser.objects.get(email=req.client)
            except CustomUser.DoesNotExist:
                req.client_user = None
        
        # Get requests awaiting client payment (professional accepted, waiting for payment)
        awaiting_payment_requests = professional_requests.filter(
            status='awaiting_payment'
        ).select_related('transaction', 'conversation').order_by('-updated_at')[:10]
        
        # Attach client user objects to awaiting payment requests
        for req in awaiting_payment_requests:
            try:
                req.client_user = CustomUser.objects.get(email=req.client)
            except CustomUser.DoesNotExist:
                req.client_user = None
        
        # Get active work (in progress with escrowed payment - ready to submit)
        active_work = professional_requests.filter(
            status='in_progress'
        ).select_related('transaction', 'conversation').order_by('-created_at')[:10]
        
        # Attach client user objects to active work
        for work in active_work:
            try:
                work.client_user = CustomUser.objects.get(email=work.client)
            except CustomUser.DoesNotExist:
                work.client_user = None
        
        # Get work awaiting client review
        pending_review = professional_requests.filter(
            status='under_review'
        ).select_related('transaction').order_by('-submitted_at')[:10]
        
        # Attach client user objects to pending review
        for work in pending_review:
            try:
                work.client_user = CustomUser.objects.get(email=work.client)
            except CustomUser.DoesNotExist:
                work.client_user = None
        
        context.update({
            'pending_requests': pending_requests,
            'awaiting_payment_requests': awaiting_payment_requests,
            'active_work': active_work,
            'pending_review': pending_review,
            # KPI Metrics
            'total_clients_served': total_clients_served,
            'clients_this_month': clients_this_month,
            'clients_trend': round(clients_trend, 0),
            'active_projects': active_projects,
            'pending_requests_count': pending_requests_count,
            'active_projects_trend': round(active_projects_trend, 0),
            'earnings_this_month': earnings_this_month,
            'avg_earning_per_project': avg_earning_per_project,
            'earnings_trend': round(earnings_trend, 0),
            'avg_rating': round(avg_rating, 1) if avg_rating > 0 else 0,
            'total_reviews': total_reviews,
        })
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
        
        # Get requests with pending payment
        # Legacy pending_payments removed to avoid duplicate banners on dashboard
        
        # Get requests awaiting payment (professional accepted, client needs to pay)
        awaiting_payment_requests = ServiceRequest.objects.filter(
            client=user.email,
            status='awaiting_payment'
        ).select_related('transaction', 'conversation').order_by('-updated_at')[:5]
        
        # Attach professional user objects to awaiting payment requests
        for req in awaiting_payment_requests:
            if req.professional:
                try:
                    req.professional_user = CustomUser.objects.get(email=req.professional)
                except CustomUser.DoesNotExist:
                    req.professional_user = None
            else:
                req.professional_user = None
        
        # Get work awaiting review
        pending_reviews = ServiceRequest.objects.filter(
            client=user.email,
            status='under_review'
        ).select_related('transaction').order_by('-submitted_at')[:5]
        
        # Add to context
        context.update({
            'metrics': metrics,
            'recent_activities': formatted_activities,
            'active_requests_tracking': active_requests_data,
            'recommended_professionals': recommended_professionals,
            'awaiting_payment_requests': awaiting_payment_requests,
            'pending_reviews': pending_reviews,
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
def professionals_api(request):
    """
    Lightweight JSON endpoint to list professionals for selection modals.
    Supports ?q=, ?page=, and returns minimal fields.
    """
    q = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1) or 1)
    per_page = int(request.GET.get('per_page', 12) or 12)

    qs = ProfessionalProfile.objects.filter(
        user__is_active=True
    ).select_related('user')

    if q:
        qs = qs.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(specializations__name__icontains=q)
        ).distinct()

    paginator = Paginator(qs.order_by('-average_rating', '-total_reviews'), per_page)
    page_obj = paginator.get_page(page)

    data = [{
        'id': prof.id,
        'email': prof.user.email,
        'name': prof.user.get_full_name() or prof.user.username or prof.user.email,
        'avatar': prof.user.get_profile_picture(),
        'average_rating': float(prof.average_rating or 0),
        'total_reviews': prof.total_reviews,
        'hourly_rate': float(prof.hourly_rate or 0),
        'consultation_fee': float(prof.consultation_fee or 0),
        'is_available': prof.is_available,
    } for prof in page_obj]

    return JsonResponse({
        'results': data,
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
        'total': paginator.count,
        'per_page': per_page,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    })

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
    
    # Check if user has saved this professional (only if authenticated)
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedProfessional.objects.filter(
            user=request.user,
            professional=professional
        ).exists()
    
    # Get similar professionals (same specializations, exclude current)
    specialization_ids = professional.specializations.values_list('id', flat=True)
    similar_professionals = ProfessionalProfile.objects.filter(
        specializations__id__in=specialization_ids
    ).exclude(
        id=professional.id
    ).select_related('user').prefetch_related('specializations').distinct()[:3]
    
    context = {
        'professional': professional,
        'is_saved': is_saved,
        'similar_professionals': similar_professionals,
    }
    
    return render(request, 'professionals/professional_detail.html', context)


@login_required
def save_professional(request, pk):
    """
    Save/unsave (toggle bookmark) a professional (AJAX endpoint)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        professional = ProfessionalProfile.objects.get(pk=pk)
        
        # Check if already saved
        saved_entry = SavedProfessional.objects.filter(
            user=request.user,
            professional=professional
        ).first()
        
        if saved_entry:
            # Already saved, so unsave it
            saved_entry.delete()
            return JsonResponse({
                'success': True,
                'saved': False,
                'message': 'Professional removed from saved list'
            })
        else:
            # Not saved yet, so save it
            SavedProfessional.objects.create(
                user=request.user,
                professional=professional
            )
            return JsonResponse({
                'success': True,
                'saved': True,
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
    # Refresh user from database to get latest profile_picture
    user = request.user
    print(f"👤 Profile - Before refresh: User {user.id}, profile_picture: {user.profile_picture}")
    user.refresh_from_db()
    print(f"👤 Profile - After refresh: User {user.id}, profile_picture: {user.profile_picture}")
    
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
def check_profile_picture(request):
    """
    Diagnostic endpoint to check profile picture in database
    """
    user = request.user
    
    return JsonResponse({
        'user_id': user.id,
        'username': user.username,
        'profile_picture_in_db': user.profile_picture,
        'profile_picture_type': str(type(user.profile_picture)),
        'is_empty': not bool(user.profile_picture),
    })

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
        
        print(f"📥 Upload response: {storage_response}")
        
        # Get public URL - extract the actual URL string
        public_url_response = supabase.storage.from_('avatars').get_public_url(file_path)
        
        # Handle both string and object responses
        if isinstance(public_url_response, str):
            public_url = public_url_response
        elif isinstance(public_url_response, dict) and 'publicUrl' in public_url_response:
            public_url = public_url_response['publicUrl']
        else:
            # Fallback: construct URL manually
            public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/avatars/{file_path}"
        
        print(f"✅ Supabase URL: {public_url}")
        print(f"🔍 URL type: {type(public_url)}")
        
        # Update user's profile_picture field
        print(f"🔍 Before save - User ID: {request.user.id}, Current URL: {request.user.profile_picture}")
        request.user.profile_picture = public_url
        request.user.save(update_fields=['profile_picture'])
        
        # Verify it was saved  
        request.user.refresh_from_db()
        print(f"🔍 After save - Verified URL in DB: {request.user.profile_picture}")
        
        # Double check by querying the database directly
        from .models import CustomUser
        db_user = CustomUser.objects.get(id=request.user.id)
        print(f"🔍 Direct DB query - User {db_user.id} profile_picture: {db_user.profile_picture}")
        
        # CRITICAL: Update the session to force Django to reload user on next request
        # This ensures the cached user in the session is invalidated
        from django.contrib.auth import update_session_auth_hash
        request.session.modified = True
        request.session.save()
        print(f"🔍 Session updated - cache invalidated")
        
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


@login_required
def accept_request(request, request_id):
    """
    Accept a service request, set price, and create transaction
    """
    if request.method != 'POST':
        return redirect('dashboard')
    
    # Get the service request
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    # Verify the current user is the assigned professional
    if service_request.professional != request.user.email:
        messages.error(request, "You don't have permission to accept this request.")
        return redirect('dashboard')
    
    # Check if already accepted
    if service_request.status != 'pending':
        messages.warning(request, "This request has already been processed.")
        return redirect('dashboard')
    
    # Get price from form
    try:
        price = request.POST.get('price')
        if not price:
            messages.error(request, "Please provide a price for this service.")
            return redirect('dashboard')
        
        price = float(price)
        if price <= 0:
            messages.error(request, "Price must be greater than 0.")
            return redirect('dashboard')
    except (ValueError, TypeError):
        messages.error(request, "Invalid price format.")
        return redirect('dashboard')
    
    try:
        from messaging.models import Conversation
        from transactions.models import Transaction
        from decimal import Decimal
        
        # Update request with price and set status to 'awaiting_payment' so client sees Pay Now
        service_request.price = Decimal(str(price))
        service_request.status = 'awaiting_payment'  # Client needs to pay
        service_request.save()
        
        # Get client user
        client_user = get_object_or_404(CustomUser, email=service_request.client)
        
        # Create conversation
        conversation = Conversation.objects.create(
            request=service_request,
            client=client_user,
            professional=request.user
        )
        
        # Create transaction
        transaction = Transaction.objects.create(
            request=service_request,
            client=client_user,
            professional=request.user,
            amount=Decimal(str(price)),
            status='pending_payment',
            payment_method='gcash'
        )
        
        messages.success(request, f"Request accepted! Price set to ₱{price:,.2f}. Client will be notified to make payment.")
        return redirect('messaging:conversation', conversation_id=conversation.id)
        
    except Exception as e:
        messages.error(request, f"Error accepting request: {str(e)}")
        return redirect('dashboard')


@login_required
def decline_request(request, request_id):
    """
    Decline a service request
    """
    if request.method != 'POST':
        return redirect('dashboard')
    
    # Get the service request
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    # Verify the current user is the assigned professional
    if service_request.professional != request.user.email:
        messages.error(request, "You don't have permission to decline this request.")
        return redirect('dashboard')
    
    # Check if already processed
    if service_request.status != 'pending':
        messages.warning(request, "This request has already been processed.")
        return redirect('dashboard')
    
    try:
        # Update request status
        service_request.status = 'declined'
        service_request.save()
        
        messages.success(request, f"Request '{service_request.title}' declined.")
        return redirect('dashboard')
        
    except Exception as e:
        messages.error(request, f"Error declining request: {str(e)}")
        return redirect('dashboard')
    
@login_required
def earnings_dashboard(request):
    # Ensure only professionals can access this
    if request.user.user_role != 'professional':
        return redirect('dashboard')
    
    professional = request.user
    
    try:
        # Calculate date ranges
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # Get transactions for this professional
        professional_transactions = Transaction.objects.filter(professional=professional)
        
        # Define completed transactions - adjust based on your business logic
        completed_transactions = professional_transactions.filter(
            Q(status='completed') | Q(paid_at__isnull=False)
        )
        
        # Total earnings (released payments)
        total_earnings = professional_transactions.filter(
            released_at__isnull=False
        ).aggregate(
            total=Sum('professional_payout')
        )['total'] or 0
        
        # Pending earnings (paid but not released)
        pending_earnings = professional_transactions.filter(
            paid_at__isnull=False,
            released_at__isnull=True
        ).aggregate(
            total=Sum('professional_payout')
        )['total'] or 0
        
        # Job statistics
        completed_jobs = completed_transactions.count()
        jobs_this_month = completed_transactions.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Average earning per job
        average_earning = completed_transactions.aggregate(
            avg=Avg('professional_payout')
        )['avg'] or 0
        
        # Earnings by service type
        earnings_by_service = completed_transactions.values(
            'request__service_type'
        ).annotate(
            total_earnings=Sum('professional_payout'),
            job_count=Count('id')
        ).order_by('-total_earnings')
        
        # Calculate percentages and clean up data
        for service in earnings_by_service:
            if total_earnings > 0:
                service['percentage'] = round((service['total_earnings'] / total_earnings) * 100, 1)
            else:
                service['percentage'] = 0
            service['service_type'] = service['request__service_type'] or 'General Service'
        
        # If no service data, provide sample
        if not earnings_by_service and total_earnings > 0:
            earnings_by_service = [
                {'service_type': 'Completed Services', 'total_earnings': total_earnings, 'percentage': 100, 'job_count': completed_jobs}
            ]
        
        # Recent transactions (last 10)
        recent_transactions = completed_transactions.select_related(
            'client', 'request'
        ).order_by('-created_at')[:10]
        
        # Chart data (last 30 days)
        chart_data = []
        chart_labels = []
        
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            daily_earnings = completed_transactions.filter(
                created_at__date=date
            ).aggregate(
                total=Sum('professional_payout')
            )['total'] or 0
            
            chart_data.append(float(daily_earnings))
            chart_labels.append(date.strftime('%b %d'))
        
        context = {
            'total_earnings': total_earnings,
            'pending_earnings': pending_earnings,
            'completed_jobs': completed_jobs,
            'completed_this_month': jobs_this_month,
            'average_earning': average_earning,
            'earnings_by_service': earnings_by_service,
            'recent_transactions': recent_transactions,
            'jobs_this_month': jobs_this_month,
            'avg_rating': getattr(professional, 'rating', 4.5),
            'repeat_clients_percentage': 65,
            'completion_rate': 95,
            'chart_data': chart_data,
            'chart_labels': chart_labels,
        }
        
    except Exception as e:
        # Fallback to sample data if there's any error
        print(f"Error in earnings dashboard: {e}")
        context = {
            'total_earnings': 12500.00,
            'pending_earnings': 2500.00,
            'completed_jobs': 45,
            'completed_this_month': 12,
            'average_earning': 277.78,
            'earnings_by_service': [
                {'service_type': 'Web Development', 'total_earnings': 8000, 'percentage': 64, 'job_count': 25},
                {'service_type': 'Consultation', 'total_earnings': 3000, 'percentage': 24, 'job_count': 15},
                {'service_type': 'Maintenance', 'total_earnings': 1500, 'percentage': 12, 'job_count': 5},
            ],
            'recent_transactions': [],
            'jobs_this_month': 12,
            'avg_rating': 4.8,
            'repeat_clients_percentage': 65,
            'completion_rate': 95,
            'chart_data': [0, 150, 300, 200, 400, 350, 500, 450, 600, 550, 700, 650, 800, 750, 900, 850, 1000, 950, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500, 1450, 1600, 1550],
            'chart_labels': ['Oct 19', 'Oct 20', 'Oct 21', 'Oct 22', 'Oct 23', 'Oct 24', 'Oct 25', 'Oct 26', 'Oct 27', 'Oct 28', 'Oct 29', 'Oct 30', 'Oct 31', 'Nov 1', 'Nov 2', 'Nov 3', 'Nov 4', 'Nov 5', 'Nov 6', 'Nov 7', 'Nov 8', 'Nov 9', 'Nov 10', 'Nov 11', 'Nov 12', 'Nov 13', 'Nov 14', 'Nov 15', 'Nov 16', 'Nov 17'],
        }
    
    # Updated template path to match your folder structure
    return render(request, 'professionals/professional_earnings.html', context)


@login_required
def reviews_page(request):
    """
    Reviews page showing reviews received and reviews given
    """
    user = request.user
    from analytics.models import Review
    from requests.models import Request as ServiceRequest
    
    # Get reviews received (where user is the reviewee)
    # For students: only show reviews from professionals (is_professional_review=False)
    # For professionals: show all reviews received
    if user.user_role == 'professional':
        reviews_received = Review.objects.filter(reviewee=user).order_by('-created_at')
    else:
        # Students can only see reviews from professionals (not professional reviews of them)
        reviews_received = Review.objects.filter(
            reviewee=user,
            is_professional_review=False,
            is_visible_to_client=True
        ).order_by('-created_at')
    
    # Get reviews given (where user is the reviewer)
    reviews_given = Review.objects.filter(reviewer=user).order_by('-created_at')
    
    # Get completed requests that can still be reviewed (within 30 days)
    from django.utils import timezone
    from datetime import timedelta
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # For students: completed requests where they haven't reviewed the professional
    if user.user_role != 'professional':
        completed_requests = ServiceRequest.objects.filter(
            client=user.email,
            status='completed',
            completed_at__gte=thirty_days_ago
        )
        
        reviewable_requests = []
        for req in completed_requests:
            if req.professional:
                try:
                    professional = CustomUser.objects.get(email=req.professional)
                    # Check if already reviewed
                    existing_review = Review.objects.filter(
                        request=req,
                        reviewer=user,
                        reviewee=professional,
                        is_professional_review=False
                    ).exists()
                    if not existing_review:
                        reviewable_requests.append({
                            'request': req,
                            'reviewee': professional,
                            'reviewee_name': professional.get_full_name() or professional.username
                        })
                except CustomUser.DoesNotExist:
                    pass
    else:
        # For professionals: completed requests where they haven't reviewed the client
        completed_requests = ServiceRequest.objects.filter(
            professional=user.email,
            status='completed',
            completed_at__gte=thirty_days_ago
        )
        
        reviewable_requests = []
        for req in completed_requests:
            try:
                client = CustomUser.objects.get(email=req.client)
                # Check if already reviewed
                existing_review = Review.objects.filter(
                    request=req,
                    reviewer=user,
                    reviewee=client,
                    is_professional_review=True
                ).exists()
                if not existing_review:
                    reviewable_requests.append({
                        'request': req,
                        'reviewee': client,
                        'reviewee_name': client.get_full_name() or client.username
                    })
            except CustomUser.DoesNotExist:
                pass
    
    context = {
        'reviews_received': reviews_received,
        'reviews_given': reviews_given,
        'reviewable_requests': reviewable_requests,
        'user': user,
        'user_role': user.user_role if hasattr(user, 'user_role') else 'client',
    }
    
    return render(request, 'users/reviews.html', context)


@login_required
def submit_review(request, request_id):
    """
    Submit a review for a completed request
    Only allowed if:
    - Request is completed
    - Within 30 days of completion
    - User hasn't already reviewed
    - User is either client or professional for this request
    """
    from analytics.models import Review
    from requests.models import Request as ServiceRequest
    from django.utils import timezone
    from datetime import timedelta
    
    user = request.user
    
    # Get the request
    try:
        req = ServiceRequest.objects.get(id=request_id)
    except ServiceRequest.DoesNotExist:
        messages.error(request, "Request not found.")
        return redirect('dashboard')
    
    # Validate user has access to this request
    if user.email != req.client and user.email != req.professional:
        messages.error(request, "You don't have permission to review this request.")
        return redirect('dashboard')
    
    # Validate request is completed
    if req.status != 'completed':
        messages.error(request, "You can only review completed requests.")
        return redirect('request_detail', request_id=request_id)
    
    # Validate within 30 days
    if not req.completed_at:
        messages.error(request, "This request doesn't have a completion date.")
        return redirect('request_detail', request_id=request_id)
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    if req.completed_at < thirty_days_ago:
        messages.error(request, "Review period has expired. Reviews must be submitted within 30 days of completion.")
        return redirect('request_detail', request_id=request_id)
    
    # Determine reviewee
    if user.email == req.client:
        # Client reviewing professional
        try:
            reviewee = CustomUser.objects.get(email=req.professional)
            is_professional_review = False
        except CustomUser.DoesNotExist:
            messages.error(request, "Professional not found.")
            return redirect('request_detail', request_id=request_id)
    else:
        # Professional reviewing client
        try:
            reviewee = CustomUser.objects.get(email=req.client)
            is_professional_review = True
        except CustomUser.DoesNotExist:
            messages.error(request, "Client not found.")
            return redirect('professional_request_detail', request_id=request_id)
    
    # Check if already reviewed
    existing_review = Review.objects.filter(
        request=req,
        reviewer=user,
        reviewee=reviewee
    ).first()
    
    if existing_review:
        messages.error(request, "You have already submitted a review for this request.")
        if user.email == req.client:
            return redirect('request_detail', request_id=request_id)
        else:
            return redirect('professional_request_detail', request_id=request_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        
        # Validate rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                messages.error(request, "Rating must be between 1 and 5.")
                return redirect('reviews_page')
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating.")
            return redirect('reviews_page')
        
        # Create review
        review = Review.objects.create(
            request=req,
            reviewer=user,
            reviewee=reviewee,
            rating=rating,
            comment=comment,
            is_professional_review=is_professional_review
        )
        
        messages.success(request, "Review submitted successfully!")
        
        # Redirect based on user role
        if user.email == req.client:
            return redirect('request_detail', request_id=request_id)
        else:
            return redirect('professional_request_detail', request_id=request_id)
    
    # GET request - show form
    context = {
        'request': req,
        'reviewee': reviewee,
        'reviewee_name': reviewee.get_full_name() or reviewee.username,
        'is_professional_review': is_professional_review,
    }
    
    return render(request, 'users/submit_review.html', context)
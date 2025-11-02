
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from supabase import create_client, Client
import json

# Initialize Supabase client
def get_supabase_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

def landing(request):
	return render(request, "landing.html")

def dashboard(request):
    # Check if user is authenticated
    if not request.session.get('user_id'):
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("login")
    
    # Get user info from session
    user_email = request.session.get('user_email', 'User')
    user_role = request.session.get('user_role', 'student')
    
    # --- ADD THIS LINE TO GET THE FIRST NAME ---
    user_first_name = request.session.get('first_name', '')
    
    # Use the first name for display, falling back to email if name is empty
    # We use .title() for consistent capitalization if the name exists
    display_name = user_first_name.title() if user_first_name else user_email
    
    # Define the context dictionary
    context = {
        # CHANGE: Pass the 'display_name' instead of 'user_email' for welcome message
        "display_name": display_name, 
        "user_email": user_email,
        "user_role": user_role
    }
    
    # Route to appropriate dashboard based on role
    if user_role == 'professional':
        return render(request, "dashboard_professional.html", context)
    else:  # student or worker (client)
        return render(request, "dashboard_client.html", context)

def logout(request):
	# Clear session data
	request.session.flush()
	messages.success(request, "You have been logged out successfully.")
	return redirect("landing")

def registration_success(request):
	# Check if user came from successful registration
	if not request.session.get('registration_success'):
		return redirect("signup")
	
	# Get registration data
	email = request.session.get('registered_email', '')
	name = request.session.get('registered_name', '')
	
	# Clear registration success flag
	request.session.pop('registration_success', None)
	request.session.pop('registered_email', None)
	request.session.pop('registered_name', None)
	
	return render(request, "users/registration_success.html", {
		"email": email,
		"name": name
	})

def login(request):
	error = None
	if request.method == "POST":
		email = request.POST.get("email")
		password = request.POST.get("password")
		
		try:
			# Initialize Supabase client
			supabase = get_supabase_client()
			
			# Authenticate with Supabase
			response = supabase.auth.sign_in_with_password({
				"email": email,
				"password": password
			})
			
			if response.user:
				# Get user metadata
				user_metadata = response.user.user_metadata or {}
				user_role = user_metadata.get('role', 'student')  # default to student
				
				# Store user session
				request.session['user_id'] = response.user.id
				request.session['user_email'] = response.user.email
				request.session['user_role'] = user_role  # Add role to session
				request.session['access_token'] = response.session.access_token
				request.session['refresh_token'] = response.session.refresh_token
				
				request.session['first_name'] = user_metadata.get('first_name', '') 
				request.session['access_token'] = response.session.access_token
				request.session['refresh_token'] = response.session.refresh_token
				messages.success(request, "Login successful!")
				return redirect("dashboard")
			else:
				error = "Invalid email or password."
				
		except Exception as e:
			error = f"Login failed: {str(e)}"
			
	return render(request, "users/login.html", {"error": error})

def signup(request):
	error = None
	if request.method == "POST":
		# Get form data
		first_name = request.POST.get("first_name")
		last_name = request.POST.get("last_name")
		email = request.POST.get("email")
		password1 = request.POST.get("password1")
		password2 = request.POST.get("password2")
		role = request.POST.get("role")
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
		if not all([first_name, last_name, email, password1, password2, role, terms]):
			error = "Please fill in all required fields."
		elif password1 != password2:
			error = "Passwords do not match."
		elif len(password1) < 8:
			error = "Password must be at least 8 characters long."
		else:
			# Create user account with Supabase
			try:
				# Initialize Supabase client
				supabase = get_supabase_client()
				
				# Prepare user metadata based on role
				user_metadata = {
					"first_name": first_name,
					"last_name": last_name,
					"role": role
				}
				
				# Add role-specific data
				if role == "professional":
					if profession:
						user_metadata["profession"] = other_profession if profession == "other" else profession
					if experience:
						user_metadata["experience"] = experience
				elif role == "student":
					if school_name:
						user_metadata["school_name"] = school_name
					if major:
						user_metadata["major"] = major
					if year_level:
						user_metadata["year_level"] = year_level
					if graduation_year:
						user_metadata["graduation_year"] = graduation_year
				elif role == "worker":
					if company_name:
						user_metadata["company_name"] = company_name
					if job_title:
						user_metadata["job_title"] = job_title
				
				# Sign up with Supabase
				response = supabase.auth.sign_up({
					"email": email,
					"password": password1,
					"options": {
						"data": user_metadata
					}
				})
				
				if response.user:
					# Registration successful - redirect to success page
					request.session['registration_success'] = True
					request.session['registered_email'] = email
					request.session['registered_name'] = f"{first_name} {last_name}"
					return redirect("registration_success")
				else:
					error = "Failed to create account. Please try again."
					
			except Exception as e:
				error = f"Registration failed: {str(e)}"
	
	return render(request, "users/signup.html", {"error": error})

def terms(request):
    return render(request, 'users/terms.html')

def privacy(request):
    return render(request, 'users/privacy.html')

def dashboard_client(request):
    # Check if user is authenticated
    if not request.session.get('user_id'):
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("login")
    
    # Get user info from session
    user_email = request.session.get('user_email', 'User')
    user_role = request.session.get('user_role', 'student')
    user_first_name = request.session.get('first_name', '')
    
    # Use the first name for display, falling back to email if name is empty
    display_name = user_first_name.title() if user_first_name else user_email
    
    context = {
        "display_name": display_name,
        "user_email": user_email,
        "user_role": user_role
    }
    
    return render(request, 'dashboard_client.html', context)

def client_profile(request):
    # Check if user is authenticated
    if not request.session.get('user_id'):
        messages.error(request, "Please log in to access your profile.")
        return redirect("login")

    # Get the access token from session
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, "Session expired. Please log in again.")
        return redirect("login")

    try:
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        # Get user data from Supabase using the access token
        response = supabase.auth.get_user(access_token)
        user = response.user
        if not user:
            messages.error(request, "User not found. Please log in again.")
            return redirect("login")

        user_metadata = user.user_metadata or {}
        first_name = user_metadata.get('first_name', '')
        last_name = user_metadata.get('last_name', '')
        user_email = user.email
        display_name = f"{first_name} {last_name}".strip() if first_name or last_name else user_email

        # Also, we can get other information from the user_metadata, such as role, profession, etc.
        # But note: the profile page is for clients, so we might want to display client-specific data.

        context = {
            "first_name": first_name,
            "last_name": last_name,
            "user_email": user_email,
            "display_name": display_name,
            # Add other fields you want to display from user_metadata
            "role": user_metadata.get('role', ''),
            "profession": user_metadata.get('profession', ''),
            "company_name": user_metadata.get('company_name', ''),
            "job_title": user_metadata.get('job_title', ''),
            "school_name": user_metadata.get('school_name', ''),
            "major": user_metadata.get('major', ''),
            "year_level": user_metadata.get('year_level', ''),
            "graduation_year": user_metadata.get('graduation_year', ''),
            "experience": user_metadata.get('experience', ''),
        }
        return render(request, 'users/client_profile.html', context)

    except Exception as e:
        messages.error(request, f"Error retrieving profile: {str(e)}")
        return redirect("dashboard")


# ========== PROFESSIONALS VIEWS ==========

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import ProfessionalProfile, Specialization, SavedProfessional, CustomUser
import json


def find_professionals(request):
    """
    Main view for browsing and searching professionals
    """
    # Check if user is authenticated via Supabase session
    if not request.session.get('user_id'):
        messages.error(request, "Please log in to browse professionals.")
        return redirect("login")
    
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


def professional_detail(request, pk):
    """
    Detailed view of a single professional
    """
    # Check if user is authenticated via Supabase session
    if not request.session.get('user_id'):
        messages.error(request, "Please log in to view professional details.")
        return redirect("login")
    
    professional = get_object_or_404(
        ProfessionalProfile.objects.select_related('user').prefetch_related('specializations'),
        pk=pk
    )
    
    # Increment profile views
    professional.profile_views += 1
    professional.save(update_fields=['profile_views'])
    
    # Get current user from session
    user_email = request.session.get('user_email')
    try:
        current_user = CustomUser.objects.get(email=user_email)
        # Check if user has saved this professional
        is_saved = SavedProfessional.objects.filter(
            user=current_user,
            professional=professional
        ).exists()
    except CustomUser.DoesNotExist:
        is_saved = False
    
    context = {
        'professional': professional,
        'is_saved': is_saved,
    }
    
    return render(request, 'professionals/professional_detail.html', context)


def save_professional(request, pk):
    """
    Save/bookmark a professional (AJAX endpoint)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    # Check if user is authenticated via Supabase session
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'message': 'Please log in to save professionals'})
    
    try:
        professional = ProfessionalProfile.objects.get(pk=pk)
        
        # Get current user from session
        user_email = request.session.get('user_email')
        current_user = CustomUser.objects.get(email=user_email)
        
        # Create saved professional entry
        saved_prof, created = SavedProfessional.objects.get_or_create(
            user=current_user,
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
    except CustomUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


def unsave_professional(request, pk):
    """
    Unsave/remove bookmark from a professional (AJAX endpoint)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    # Check if user is authenticated via Supabase session
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'message': 'Please log in to unsave professionals'})
    
    try:
        professional = ProfessionalProfile.objects.get(pk=pk)
        
        # Get current user from session
        user_email = request.session.get('user_email')
        current_user = CustomUser.objects.get(email=user_email)
        
        # Delete saved professional entry
        SavedProfessional.objects.filter(
            user=current_user,
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
    except CustomUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


def saved_professionals_list(request):
    """
    List of saved professionals for the current user
    """
    # Check if user is authenticated via Supabase session
    if not request.session.get('user_id'):
        messages.error(request, "Please log in to view saved professionals.")
        return redirect("login")
    
    # Get current user from session
    user_email = request.session.get('user_email')
    try:
        current_user = CustomUser.objects.get(email=user_email)
        saved = SavedProfessional.objects.filter(
            user=current_user
        ).select_related('professional__user').prefetch_related('professional__specializations').order_by('-saved_at')
    except CustomUser.DoesNotExist:
        saved = SavedProfessional.objects.none()
    
    context = {
        'saved_professionals': saved,
    }
    
    return render(request, 'professionals/saved_professionals.html', context)

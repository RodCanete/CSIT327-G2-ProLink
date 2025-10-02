
from django.shortcuts import render, redirect
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
	
	return render(request, "dashboard.html", {"user_email": user_email})

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
				# Store user session
				request.session['user_id'] = response.user.id
				request.session['user_email'] = response.user.email
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
				
				# Sign up with Supabase
				response = supabase.auth.sign_up({
					"email": email,
					"password": password1,
					"options": {
						"data": {
							"first_name": first_name,
							"last_name": last_name,
							"role": role
						}
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

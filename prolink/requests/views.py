from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
from supabase import create_client, Client
import json
import os
import uuid
from .models import Request, RequestMessage

# Initialize Supabase client
def get_supabase_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

def requests_list(request):
    # Check if user is authenticated
    if not request.session.get('user_id'):
        messages.error(request, "Please log in to view your requests.")
        return redirect("login")
    
    user_email = request.session.get('user_email', '')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Query real requests from database
    user_requests = Request.objects.filter(client=user_email).order_by('-created_at')
    
    # Calculate counts for each status
    all_requests_count = user_requests.count()
    pending_count = user_requests.filter(status='pending').count()
    in_progress_count = user_requests.filter(status='in_progress').count()
    completed_count = user_requests.filter(status='completed').count()
    cancelled_count = user_requests.filter(status='cancelled').count()
    
    # Apply filters
    filtered_requests = user_requests
    
    if status_filter != 'all':
        filtered_requests = filtered_requests.filter(status=status_filter)
    
    if search_query:
        filtered_requests = filtered_requests.filter(
            models.Q(title__icontains=search_query) | 
            models.Q(professional__icontains=search_query)
        )
    
    # Convert to list of dictionaries for template compatibility
    requests_list = []
    for req in filtered_requests:
        # Calculate progress based on status
        progress = 0
        if req.status == 'in_progress':
            progress = 60  # Default progress for in_progress
        elif req.status == 'completed':
            progress = 100
        elif req.status == 'pending':
            progress = 0
        
        requests_list.append({
            'id': req.id,
            'title': req.title,
            'description': req.description,
            'professional': req.professional,
            'status': req.status,
            'price': float(req.price) if req.price else None,
            'timeline_days': req.timeline_days,
            'created_at': req.created_at.strftime('%Y-%m-%d'),
            'updated_at': req.updated_at.strftime('%Y-%m-%d'),
            'progress': progress
        })
    
    context = {
        'requests': requests_list,
        'current_status': status_filter,
        'search_query': search_query,
        'user_email': user_email,
        'user_role': request.session.get('user_role', 'student'),
        'all_requests_count': all_requests_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count
    }
    
    return render(request, 'requests/requests.html', context)

def request_detail(request, request_id):
    # Check if user is authenticated
    if not request.session.get('user_id'):
        messages.error(request, "Please log in to view request details.")
        return redirect("login")
    
    user_email = request.session.get('user_email', '')
    
    # Get the request
    try:
        req = Request.objects.get(id=request_id, client=user_email)
    except Request.DoesNotExist:
        messages.error(request, "Request not found or you don't have permission to view it.")
        return redirect('requests_list')
    
    # Get messages for this request
    messages_list = RequestMessage.objects.filter(request=req).order_by('created_at')
    
    # Parse attached files
    attached_files = []
    if req.attached_files:
        try:
            attached_files = json.loads(req.attached_files)
        except json.JSONDecodeError:
            attached_files = []
    
    # Calculate progress based on status
    progress = 0
    if req.status == 'in_progress':
        progress = 60  # Default progress for in_progress
    elif req.status == 'completed':
        progress = 100
    elif req.status == 'pending':
        progress = 0
    
    # Format request data for template
    request_data = {
        'id': req.id,
        'title': req.title,
        'description': req.description,
        'professional': req.professional,
        'status': req.status,
        'price': float(req.price) if req.price else None,
        'timeline_days': req.timeline_days,
        'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at': req.updated_at.strftime('%Y-%m-%d %H:%M'),
        'completed_at': req.completed_at.strftime('%Y-%m-%d %H:%M') if req.completed_at else None,
        'progress': progress,
        'attached_files': attached_files,
        'messages': [
            {
                'id': msg.id,
                'sender_email': msg.sender_email,
                'message': msg.message,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_from_professional': msg.is_from_professional
            }
            for msg in messages_list
        ]
    }
    
    context = {
        'request': request_data,
        'user_email': user_email,
        'user_role': request.session.get('user_role', 'student')
    }
    
    return render(request, 'requests/request_detail.html', context)

def create_request(request):
    # Check if user is authenticated
    if not request.session.get('user_id'):
        messages.error(request, "Please log in to create a request.")
        return redirect("login")
    
    user_email = request.session.get('user_email', '')
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', '')
        price = request.POST.get('price', '')
        timeline_days = request.POST.get('timeline_days', '')
        professional = request.POST.get('professional', '').strip()
        priority = request.POST.get('priority', 'medium')
        
        # Validate required fields
        errors = []
        if not title or len(title) < 5:
            errors.append("Title must be at least 5 characters long.")
        if len(title) > 200:
            errors.append("Title must be less than 200 characters.")
        if not description or len(description) < 50:
            errors.append("Description must be at least 50 characters long.")
        if len(description) > 5000:
            errors.append("Description must be less than 5000 characters.")
        if not timeline_days or not timeline_days.isdigit():
            errors.append("Timeline must be a valid number of days.")
        elif int(timeline_days) < 1 or int(timeline_days) > 365:
            errors.append("Timeline must be between 1 and 365 days.")
        
        # Validate price if provided
        if price:
            try:
                price_float = float(price)
                if price_float < 0:
                    errors.append("Price must be a positive number.")
            except ValueError:
                errors.append("Price must be a valid number.")
        
        # Handle file uploads
        attached_files = []
        if 'attached_files' in request.FILES:
            files = request.FILES.getlist('attached_files')
            if len(files) > 5:
                errors.append("Maximum 5 files allowed.")
            else:
                for file in files:
                    # Check file size (10MB limit)
                    if file.size > 10 * 1024 * 1024:
                        errors.append(f"File {file.name} is too large. Maximum size is 10MB.")
                        continue
                    
                    # Check file type
                    allowed_types = ['.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg', '.zip']
                    file_ext = os.path.splitext(file.name)[1].lower()
                    if file_ext not in allowed_types:
                        errors.append(f"File {file.name} has unsupported format. Allowed: PDF, DOC, DOCX, PNG, JPG, ZIP")
                        continue
                    
                    # Save file
                    try:
                        # Generate unique filename
                        file_extension = os.path.splitext(file.name)[1]
                        unique_filename = f"{uuid.uuid4()}{file_extension}"
                        file_path = default_storage.save(f"request_files/{unique_filename}", file)
                        attached_files.append({
                            'original_name': file.name,
                            'saved_name': file_path,
                            'size': file.size
                        })
                    except Exception as e:
                        errors.append(f"Error uploading file {file.name}: {str(e)}")
        
        if errors:
            # Return form with errors
            context = {
                'title': title,
                'description': description,
                'category': category,
                'price': price,
                'timeline_days': timeline_days,
                'professional': professional,
                'priority': priority,
                'errors': errors,
                'user_email': user_email,
                'user_role': request.session.get('user_role', 'student')
            }
            return render(request, 'requests/create_request.html', context)
        
        # Create the request
        try:
            request_obj = Request.objects.create(
                title=title,
                description=description,
                client=user_email,
                professional=professional,
                status='pending',
                price=float(price) if price else None,
                timeline_days=int(timeline_days),
                attached_files=json.dumps(attached_files) if attached_files else ''
            )
            
            messages.success(request, f"Request '{title}' created successfully!")
            return redirect('requests_list')
            
        except Exception as e:
            messages.error(request, f"Error creating request: {str(e)}")
            context = {
                'title': title,
                'description': description,
                'category': category,
                'price': price,
                'timeline_days': timeline_days,
                'professional': professional,
                'priority': priority,
                'errors': [f"Error creating request: {str(e)}"],
                'user_email': user_email,
                'user_role': request.session.get('user_role', 'student')
            }
            return render(request, 'requests/create_request.html', context)
    
    # GET request - show form
    context = {
        'user_email': user_email,
        'user_role': request.session.get('user_role', 'student')
    }
    return render(request, 'requests/create_request.html', context)

@csrf_exempt
def send_message(request, request_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_text = data.get('message', '')
            
            if not message_text:
                return JsonResponse({'success': False, 'error': 'Message cannot be empty'})
            
            # In a real implementation, you would save to database
            # For now, just return success
            return JsonResponse({'success': True, 'message': 'Message sent successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def cancel_request(request, request_id):
    if request.method == 'POST':
        try:
            # In a real implementation, you would update the request status
            return JsonResponse({'success': True, 'message': 'Request cancelled successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
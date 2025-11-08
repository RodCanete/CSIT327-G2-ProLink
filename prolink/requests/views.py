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
import decimal
from .models import Request, RequestMessage
from .storage_utils import get_storage_manager
from users.models import CustomUser

# Initialize Supabase client
def get_supabase_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

def requests_list(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to view your requests.")
        return redirect("login")
    
    user_email = request.user.email
    
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
        
        # Safely convert price to float, handling invalid decimals
        try:
            price_value = float(req.price) if req.price else None
        except (ValueError, TypeError, decimal.InvalidOperation):
            price_value = None
        
        requests_list.append({
            'id': req.id,
            'title': req.title,
            'description': req.description,
            'professional': req.professional,
            'status': req.status,
            'price': price_value,
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
        'user_role': request.user.user_role if hasattr(request.user, 'user_role') else 'client',
        'user': request.user,
        'all_requests_count': all_requests_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count
    }
    
    return render(request, 'requests/requests.html', context)

def request_detail(request, request_id):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to view request details.")
        return redirect("login")
    
    user_email = request.user.email
    
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
    
    # Format messages for template
    formatted_messages = [
        {
            'id': msg.id,
            'sender_email': msg.sender_email,
            'message': msg.message,
            'created_at': msg.created_at.strftime('%b %d, %Y at %I:%M %p'),
            'is_from_professional': msg.is_from_professional
        }
        for msg in messages_list
    ]
    
    # Create a namespace object for the request data to work better with template
    class RequestData:
        pass
    
    request_data = RequestData()
    request_data.id = req.id
    request_data.title = req.title
    request_data.description = req.description
    request_data.professional = req.professional
    request_data.status = req.status
    request_data.price = req.price  # Keep as Decimal for template
    request_data.timeline_days = req.timeline_days
    request_data.created_at = req.created_at.strftime('%b %d, %Y at %I:%M %p')
    request_data.updated_at = req.updated_at.strftime('%b %d, %Y at %I:%M %p')
    request_data.completed_at = req.completed_at.strftime('%b %d, %Y at %I:%M %p') if req.completed_at else None
    request_data.progress = progress
    request_data.attached_files = attached_files
    request_data.messages = formatted_messages
    
    context = {
        'request': request_data,
        'user_email': user_email,
        'user_role': request.user.user_role if hasattr(request.user, 'user_role') else 'client',
        'user': request.user
    }
    
    # Check if user has already reviewed (only for completed requests)
    if req.status == 'completed' and request.user.is_authenticated:
        from analytics.models import Review
        from users.models import CustomUser
        
        # Get reviewee
        reviewee_email = req.professional if user_email == req.client else req.client
        if reviewee_email:
            try:
                reviewee = CustomUser.objects.get(email=reviewee_email)
                user_review = Review.objects.filter(
                    request=req,
                    reviewer=request.user,
                    reviewee=reviewee,
                    is_deleted=False
                ).first()
                context['user_review'] = user_review
            except CustomUser.DoesNotExist:
                context['user_review'] = None
        else:
            context['user_review'] = None
    else:
        context['user_review'] = None
    
    return render(request, 'requests/request_detail.html', context)

def create_request(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to create a request.")
        return redirect("login")
    
    user_email = request.user.email
    
    # Get all professionals for the dropdown
    professionals = CustomUser.objects.filter(user_role='professional').values('id', 'email', 'first_name', 'last_name')
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', '')
        price = request.POST.get('price', '')
        timeline_days = request.POST.get('timeline_days', '')
        professional_email = request.POST.get('professional', '').strip()
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
        
        # Validate professional selection if provided
        if professional_email:
            try:
                CustomUser.objects.get(email=professional_email, user_role='professional')
            except CustomUser.DoesNotExist:
                errors.append("Selected professional is not valid.")
        
        # Handle file uploads with Supabase Storage
        attached_files = []
        if 'attached_files' in request.FILES:
            files = request.FILES.getlist('attached_files')
            
            # Debug: Log file count
            print(f"📁 Uploading {len(files)} files for {user_email}")
            
            try:
                storage_manager = get_storage_manager()
                
                # Upload files and collect any errors
                uploaded, upload_errors = storage_manager.upload_multiple_files(
                    files, 
                    folder=f"requests/{user_email}"
                )
                
                attached_files = uploaded
                errors.extend(upload_errors)
                
                # Debug: Log upload results
                print(f"✅ Uploaded {len(uploaded)} files")
                print(f"❌ Errors: {len(upload_errors)}")
                for file_info in uploaded:
                    print(f"  - {file_info['original_name']}: {file_info['public_url']}")
                
            except Exception as e:
                error_msg = f"Error uploading files: {str(e)}"
                print(f"❌ Upload exception: {error_msg}")
                errors.append(error_msg)
        
        if errors:
            # Return form with errors
            context = {
                'title': title,
                'description': description,
                'category': category,
                'price': price,
                'timeline_days': timeline_days,
                'professional': professional_email,
                'priority': priority,
                'errors': errors,
                'user_email': user_email,
                'user_role': request.session.get('user_role', 'student'),
                'professionals': professionals
            }
            return render(request, 'requests/create_request.html', context)
        
        # Create the request
        try:
            Request.objects.create(
                title=title,
                description=description,
                client=user_email,
                professional=professional_email if professional_email else '',
                status='pending',
                price=float(price) if price else None,
                timeline_days=int(timeline_days),
                attached_files=json.dumps(attached_files) if attached_files else ''
            )
            
            success_msg = f"Request '{title}' created successfully!"
            if attached_files:
                success_msg += f" ({len(attached_files)} file(s) uploaded)"
            messages.success(request, success_msg)
            return redirect('requests_list')
            
        except Exception as e:
            messages.error(request, f"Error creating request: {str(e)}")
            context = {
                'title': title,
                'description': description,
                'category': category,
                'price': price,
                'timeline_days': timeline_days,
                'professional': professional_email,
                'priority': priority,
                'errors': [f"Error creating request: {str(e)}"],
                'user_email': user_email,
                'user_role': request.session.get('user_role', 'student'),
                'professionals': professionals
            }
            return render(request, 'requests/create_request.html', context)
    
    # GET request - show form
    context = {
        'user_email': user_email,
        'user_role': request.session.get('user_role', 'student'),
        'professionals': professionals
    }
    return render(request, 'requests/create_request.html', context)

def test_upload_page(request):
    """Test page for file uploads"""
    if request.method == 'POST':
        uploaded_files = []
        errors = []
        
        files_in_request = 'test_files' in request.FILES
        post_keys = list(request.POST.keys())
        
        if 'test_files' in request.FILES:
            files = request.FILES.getlist('test_files')
            
            try:
                storage_manager = get_storage_manager()
                uploaded, upload_errors = storage_manager.upload_multiple_files(
                    files, 
                    folder="test-uploads"
                )
                uploaded_files = uploaded
                errors = upload_errors
            except Exception as e:
                errors.append(f"Exception: {str(e)}")
        
        context = {
            'uploaded_files': uploaded_files,
            'errors': errors,
            'files_in_request': files_in_request,
            'post_keys': post_keys
        }
        return render(request, 'requests/test_upload.html', context)
    
    return render(request, 'requests/test_upload.html')

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

def delete_request(request, request_id):
    """Delete a request (only pending requests can be deleted)"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    if request.method == 'POST':
        try:
            user_email = request.user.email
            req = get_object_or_404(Request, id=request_id, client=user_email)
            
            # Only allow deletion of pending requests
            if req.status != 'pending':
                return JsonResponse({
                    'success': False, 
                    'error': 'Only pending requests can be deleted'
                }, status=400)
            
            req.delete()
            return JsonResponse({'success': True, 'message': 'Request deleted successfully'})
            
        except Request.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Request not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

def edit_request(request, request_id):
    """Edit a request with file management"""
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to edit requests.")
        return redirect("login")
    
    user_email = request.user.email
    req = get_object_or_404(Request, id=request_id, client=user_email)
    
    # Get all professionals for the dropdown
    professionals = CustomUser.objects.filter(user_role='professional').values('id', 'email', 'first_name', 'last_name')
    
    # Only allow editing of pending requests
    if req.status != 'pending':
        messages.error(request, "Only pending requests can be edited.")
        return redirect('requests_list')
    
    # Parse existing files
    existing_files = []
    if req.attached_files:
        try:
            existing_files = json.loads(req.attached_files)
        except json.JSONDecodeError:
            existing_files = []
    
    if request.method == 'POST':
        try:
            # Update request fields
            req.title = request.POST.get('title', '').strip()
            req.description = request.POST.get('description', '').strip()
            professional_email = request.POST.get('professional', '').strip()
            
            # Validate required fields
            if not req.title or len(req.title) < 5:
                messages.error(request, "Title must be at least 5 characters long.")
                return redirect('edit_request', request_id=request_id)
            
            if not req.description or len(req.description) < 50:
                messages.error(request, "Description must be at least 50 characters long.")
                return redirect('edit_request', request_id=request_id)
            
            # Update professional
            if professional_email:
                try:
                    CustomUser.objects.get(email=professional_email, user_role='professional')
                    req.professional = professional_email
                except CustomUser.DoesNotExist:
                    messages.error(request, "Selected professional is not valid.")
                    return redirect('edit_request', request_id=request_id)
            else:
                req.professional = ''
            
            # Update price
            price_str = request.POST.get('price', '').strip()
            if price_str:
                try:
                    req.price = decimal.Decimal(price_str)
                except (ValueError, decimal.InvalidOperation):
                    req.price = None
            else:
                req.price = None
            
            # Update timeline
            timeline_str = request.POST.get('timeline_days', '').strip()
            if timeline_str:
                try:
                    timeline = int(timeline_str)
                    if 1 <= timeline <= 365:
                        req.timeline_days = timeline
                except ValueError:
                    pass
            
            # Handle new file uploads
            new_files = []
            if 'attached_files' in request.FILES:
                files = request.FILES.getlist('attached_files')
                storage_manager = get_storage_manager()
                
                # Check total files (existing + new)
                total_files = len(existing_files) + len(files)
                if total_files > 5:
                    messages.error(request, f"Maximum 5 files allowed. You have {len(existing_files)} existing files.")
                    return redirect('edit_request', request_id=request_id)
                
                # Upload new files
                uploaded, upload_errors = storage_manager.upload_multiple_files(
                    files, 
                    folder=f"requests/{user_email}"
                )
                
                if upload_errors:
                    for error in upload_errors:
                        messages.error(request, error)
                    return redirect('edit_request', request_id=request_id)
                
                new_files = uploaded
            
            # Handle file deletions
            files_to_delete = request.POST.getlist('delete_files')
            if files_to_delete:
                storage_manager = get_storage_manager()
                remaining_files = []
                
                for file_data in existing_files:
                    if file_data.get('stored_path') not in files_to_delete:
                        remaining_files.append(file_data)
                    else:
                        # Delete from Supabase
                        storage_manager.delete_file(file_data.get('stored_path'))
                
                existing_files = remaining_files
            
            # Combine existing and new files
            all_files = existing_files + new_files
            req.attached_files = json.dumps(all_files) if all_files else ''
            
            req.save()
            messages.success(request, "Request updated successfully!")
            return redirect('request_detail', request_id=request_id)
            
        except Exception as e:
            messages.error(request, f"Error updating request: {str(e)}")
            return redirect('edit_request', request_id=request_id)
    
    # GET request - render the edit form
    context = {
        'request': req,
        'user': request.user,
        'existing_files': existing_files,
        'professionals': professionals
    }
    return render(request, 'requests/edit_request.html', context)
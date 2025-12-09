from django.urls import reverse
# Pay Now view for client to pay for accepted request
def pay_request(request, request_id):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to pay for your request.")
        return redirect("login")
    user_email = request.user.email
    req = get_object_or_404(Request, id=request_id, client=user_email)
    if req.status != 'awaiting_payment':
        messages.error(request, "This request is not awaiting payment.")
        return redirect('requests_list')
    # For now, just show a placeholder page or redirect to detail
    # In production, redirect to payment gateway or payment form
    return render(request, 'requests/pay_request.html', {'request': req})
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
from django.db.models import Q
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
    user_requests = Request.objects.filter(client=user_email).select_related('conversation').order_by('-created_at')
    
    # Calculate counts for each status
    all_requests_count = user_requests.count()
    pending_count = user_requests.filter(status='pending').count()
    in_progress_count = user_requests.filter(status='in_progress').count()
    completed_count = user_requests.filter(status='completed').count()
    cancelled_count = user_requests.filter(status='cancelled').count()
    declined_count = user_requests.filter(status='declined').count()
    
    # Apply filters
    filtered_requests = user_requests
    # Show both 'pending' and 'awaiting_payment' in 'pending' tab, and both 'in_progress' and 'awaiting_payment' in 'in_progress' tab
    if status_filter == 'pending':
        filtered_requests = filtered_requests.filter(status__in=['pending', 'awaiting_payment'])
    elif status_filter == 'in_progress':
        filtered_requests = filtered_requests.filter(status__in=['in_progress'])
    elif status_filter != 'all':
        filtered_requests = filtered_requests.filter(status=status_filter)
    # Default (all) shows everything
    if search_query:
        filtered_requests = filtered_requests.filter(
            models.Q(title__icontains=search_query) | 
            models.Q(professional__icontains=search_query)
        )
    # Attach professional_user objects and add progress to each request
    requests_with_data = []
    for req in filtered_requests:
        # Calculate progress based on status
        progress = 0
        if req.status == 'in_progress':
            progress = 60  # Default progress for in_progress
        elif req.status == 'completed':
            progress = 100
        elif req.status == 'pending':
            progress = 0
        elif req.status == 'awaiting_payment':
            progress = 0
        # Add progress attribute to the request object
        req.progress = progress
        
        # Attach professional_user object if professional is assigned
        if req.professional:
            try:
                req.professional_user = CustomUser.objects.get(email=req.professional)
            except CustomUser.DoesNotExist:
                req.professional_user = None
        else:
            req.professional_user = None
            
        # Attach transaction if exists
        try:
            from transactions.models import Transaction
            req.transaction = Transaction.objects.filter(request=req).first()
        except:
            req.transaction = None
            
        requests_with_data.append(req)
    
    context = {
        'requests': requests_with_data,
        'current_status': status_filter,
        'search_query': search_query,
        'user_email': user_email,
        'user_role': request.user.user_role if hasattr(request.user, 'user_role') else 'client',
        'user': request.user,
        'all_requests_count': all_requests_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'declined_count': declined_count
    }
    
    return render(request, 'requests/requests.html', context)

def request_detail(request, request_id):
    """Client view for request details (also accessible by admins)"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to view request details.")
        return redirect("login")
    
    user_email = request.user.email
    
    # Check if user is admin
    is_admin = hasattr(request.user, 'is_staff') and request.user.is_staff
    
    # Get the request - CLIENT or ADMIN
    try:
        if is_admin:
            # Admins can view any request
            req = Request.objects.get(id=request_id)
        else:
            # Regular users can only view their own requests
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
    
    # Parse deliverable files (submitted by professional)
    deliverable_files = []
    if getattr(req, 'deliverable_files', None):
        try:
            deliverable_files = json.loads(req.deliverable_files)
        except json.JSONDecodeError:
            deliverable_files = []
    
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
    request_data.client = req.client  # Needed for template condition
    request_data.status = req.status
    request_data.price = req.price  # Keep as Decimal for template
    request_data.timeline_days = req.timeline_days
    request_data.created_at = req.created_at.strftime('%b %d, %Y at %I:%M %p')
    request_data.updated_at = req.updated_at.strftime('%b %d, %Y at %I:%M %p')
    request_data.completed_at = req.completed_at.strftime('%b %d, %Y at %I:%M %p') if req.completed_at else None
    request_data.progress = progress
    request_data.attached_files = attached_files
    request_data.messages = formatted_messages
    # Include deliverables for client review
    request_data.deliverable_notes = getattr(req, 'deliverable_notes', '')
    request_data.deliverable_files = deliverable_files
    # Include revision fields for template
    request_data.revision_count = getattr(req, 'revision_count', 0)
    request_data.max_revisions = getattr(req, 'max_revisions', 3)
    request_data.revision_notes = getattr(req, 'revision_notes', '')
    
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
                    reviewee=reviewee
                ).first()
                context['user_review'] = user_review
            except CustomUser.DoesNotExist:
                context['user_review'] = None
        else:
            context['user_review'] = None
    else:
        context['user_review'] = None
    
    return render(request, 'requests/request_detail.html', context)


def professional_requests_list(request):
    """Professional view for all their client requests"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to view requests.")
        return redirect("login")
    
    # Check if user is a professional
    if request.user.user_role != 'professional':
        messages.error(request, "This page is for professionals only.")
        return redirect('dashboard')
    
    user_email = request.user.email
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'latest')  # latest, price_high, price_low
    
    # Query all requests assigned to this professional
    professional_requests = Request.objects.filter(professional=user_email)
    
    # Apply sorting
    if sort_by == 'latest':
        professional_requests = professional_requests.order_by('-created_at')
    elif sort_by == 'price_high':
        professional_requests = professional_requests.order_by('-price', '-created_at')
    elif sort_by == 'price_low':
        professional_requests = professional_requests.order_by('price', '-created_at')
    else:
        professional_requests = professional_requests.order_by('-created_at')
    
    # Calculate counts for each status
    total_count = professional_requests.count()
    pending_count = professional_requests.filter(status='pending').count()
    in_progress_count = professional_requests.filter(status='in_progress').count()
    under_review_count = professional_requests.filter(status='under_review').count()
    completed_count = professional_requests.filter(status='completed').count()
    cancelled_count = professional_requests.filter(status='cancelled').count()
    
    # Apply filters
    filtered_requests = professional_requests
    
    if status_filter != 'all':
        filtered_requests = filtered_requests.filter(status=status_filter)
    
    if search_query:
        filtered_requests = filtered_requests.filter(
            models.Q(title__icontains=search_query) | 
            models.Q(client__icontains=search_query)
        )
    
    # Attach client_user objects to each request
    requests_list = []
    for req in filtered_requests:
        try:
            req.client_user = CustomUser.objects.get(email=req.client)
        except CustomUser.DoesNotExist:
            req.client_user = None
        requests_list.append(req)
    
    context = {
        'requests': requests_list,
        'current_status': status_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'user_email': user_email,
        'user': request.user,
        'total_count': total_count,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'under_review_count': under_review_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count
    }
    
    return render(request, 'requests/professional_requests_list.html', context)


def professional_request_detail(request, request_id):
    """Professional view for request details (also accessible by admins)"""
    from users.models import CustomUser
    from transactions.models import Transaction
    from analytics.models import Review
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to view request details.")
        return redirect("login")
    
    # Check if user is admin
    is_admin = hasattr(request.user, 'is_staff') and request.user.is_staff
    
    # Check if user is a professional or admin
    if not is_admin and request.user.user_role != 'professional':
        messages.error(request, "This page is for professionals only.")
        return redirect('dashboard')
    
    user_email = request.user.email
    
    # Get the request - PROFESSIONAL or ADMIN
    try:
        if is_admin:
            # Admins can view any request
            req = Request.objects.get(id=request_id)
        else:
            # Professionals can only view requests assigned to them
            req = Request.objects.get(id=request_id, professional=user_email)
    except Request.DoesNotExist:
        messages.error(request, "Request not found or not assigned to you.")
        return redirect('dashboard')
    
    # Parse attached files
    attached_files = []
    if req.attached_files:
        try:
            attached_files = json.loads(req.attached_files)
        except json.JSONDecodeError:
            attached_files = []
    
    # Parse deliverable files (submitted by professional)
    deliverable_files = []
    if getattr(req, 'deliverable_files', None):
        try:
            deliverable_files = json.loads(req.deliverable_files)
        except json.JSONDecodeError:
            deliverable_files = []
    
    # Calculate progress based on status
    progress = 0
    if req.status == 'in_progress':
        progress = 60
    elif req.status == 'completed':
        progress = 100
    elif req.status == 'under_review':
        progress = 80
    elif req.status == 'pending':
        progress = 0
    
    # Get transaction if exists
    transaction = None
    try:
        transaction = Transaction.objects.get(request_id=req.id)
    except Transaction.DoesNotExist:
        pass
    
    # Get client user object
    client_user = CustomUser.objects.filter(email=req.client).first()
    
    # Get reviews from other professionals about this client (visible to professionals only)
    other_professional_reviews = []
    if client_user:
        other_professional_reviews = Review.objects.filter(
            reviewee=client_user,
            is_professional_review=True
        ).exclude(
            reviewer=request.user  # Exclude current professional's own review
        ).select_related('reviewer', 'request').order_by('-created_at')[:5]  # Show latest 5 reviews
    
    context = {
        'request': req,
        'service_request': req,
        'attached_files': attached_files,
        'deliverable_files': deliverable_files,
        'progress': progress,
        'transaction': transaction,
        'client': client_user,
        'other_professional_reviews': other_professional_reviews,  # Reviews from other professionals about this client
        'user': request.user
    }
    
    # Check if user has already reviewed (only for completed requests)
    if req.status == 'completed' and request.user.is_authenticated:
        
        # Get reviewee (client)
        if req.client:
            try:
                reviewee = CustomUser.objects.get(email=req.client)
                user_review = Review.objects.filter(
                    request=req,
                    reviewer=request.user,
                    reviewee=reviewee
                ).first()
                context['user_review'] = user_review
            except CustomUser.DoesNotExist:
                context['user_review'] = None
        else:
            context['user_review'] = None
    else:
        context['user_review'] = None
    
    return render(request, 'requests/professional_request_detail.html', context)


def create_request(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to create a request.")
        return redirect("login")
    
    user_email = request.user.email
    
    # Get all professionals for the dropdown
    professionals = CustomUser.objects.filter(user_role='professional')
    
    # Check if a professional is pre-selected via URL parameter
    preselected_professional_id = request.GET.get('professional')
    preselected_professional = None
    preselected_professional_email = None
    if preselected_professional_id:
        try:
            preselected_professional = CustomUser.objects.get(id=preselected_professional_id, user_role='professional')
            preselected_professional_email = preselected_professional.email
        except CustomUser.DoesNotExist:
            pass
    
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
        'professionals': professionals,
        'preselected_professional': preselected_professional,
        'preselected_professional_email': preselected_professional_email
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
    """Delete a request - clients can delete any of their requests"""
    print(f"🗑️ Delete request called: ID={request_id}, Method={request.method}, Auth={request.user.is_authenticated}")
    
    if not request.user.is_authenticated:
        print("❌ User not authenticated")
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    if request.method == 'POST':
        try:
            user_email = request.user.email
            print(f"👤 User email: {user_email}")
            req = get_object_or_404(Request, id=request_id, client=user_email)
            print(f"📝 Found request: {req.title}, Status: {req.status}")
            
            # Clients can delete any of their requests
            # But prevent deletion of in_progress requests with active transactions
            if req.status == 'in_progress':
                # Check if there's an active transaction
                try:
                    from transactions.models import Transaction
                    transaction = Transaction.objects.filter(request=req, status__in=['pending_payment', 'escrowed']).first()
                    if transaction:
                        return JsonResponse({
                            'success': False, 
                            'error': 'Cannot delete request with active payment. Please complete or cancel the transaction first.'
                        }, status=400)
                except:
                    pass
            
            req.delete()
            print(f"✅ Request {request_id} deleted successfully")
            return JsonResponse({'success': True, 'message': 'Request deleted successfully'})
            
        except Request.DoesNotExist:
            print(f"❌ Request {request_id} not found")
            return JsonResponse({'success': False, 'error': 'Request not found'}, status=404)
        except Exception as e:
            print(f"❌ Error deleting request: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    print(f"❌ Invalid method: {request.method}")
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


def accept_request(request, request_id):
    """Professional accepts or declines client's request with set price"""
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to respond to requests.")
        return redirect("login")
    
    if request.user.user_role != 'professional':
        messages.error(request, "Only professionals can respond to requests.")
        return redirect('dashboard')
    
    user_email = request.user.email
    
    # Get the request assigned to this professional
    try:
        req = Request.objects.get(id=request_id, professional=user_email, status='pending')
    except Request.DoesNotExist:
        messages.error(request, "Request not found or already processed.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            # Validate that request has a price
            if not req.price or req.price <= 0:
                messages.error(request, "Cannot accept request: No budget set by client.")
                return redirect('dashboard')
            
            # Professional accepts client's budget
            try:
                from transactions.models import Transaction
                from messaging.models import Conversation, Message
                
                # Get client user
                client_user = CustomUser.objects.filter(email__iexact=req.client).first()
                if not client_user:
                    print(f"❌ accept_request: Client user not found for email '{req.client}' (case-insensitive search)")
                    messages.error(request, f"Cannot find client user for email {req.client}. Please contact support.")
                    return redirect('professional_requests_list')
                
                # Create transaction with client's set price
                transaction = Transaction.objects.create(
                    request=req,
                    client=client_user,
                    professional=request.user,
                    amount=req.price,
                    status='pending_payment'
                )
                
                # Update request status to awaiting payment
                req.status = 'awaiting_payment'
                req.save()
                
                # Create or get conversation
                conversation, created = Conversation.objects.get_or_create(
                    request=req,
                    defaults={
                        'client': client_user,
                        'professional': request.user,
                        'is_active': True
                    }
                )
                
                # Always send a message to client to prompt payment
                try:
                    pay_url = reverse('transactions:initiate_payment', args=[transaction.id])
                except Exception as e:
                    print(f"⚠️ accept_request: Could not reverse pay URL for transaction {transaction.id}: {e}")
                    pay_url = None
                
                payment_message = (
                    f"Hello {client_user.first_name}! 👋\n\n"
                    f"I've accepted your request for '{req.title}'.\n\n"
                    f"Project Budget: ₱{req.price:,.2f}\n"
                    f"Timeline: {req.timeline_days} days\n\n"
                    f"Please proceed with the payment to start the project. "
                    f"Once payment is confirmed, I'll begin working on your request immediately.\n\n"
                    f"You can pay by clicking the 'Pay Now' button on your dashboard."
                    f"{(' Or click here: ' + pay_url) if pay_url else ''}\n\n"
                    f"Feel free to message me if you have any questions!"
                )
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=payment_message
                )
                
                # Send notification to client
                from analytics.models import Notification
                from django.urls import reverse
                try:
                    pay_url = reverse('transactions:initiate_payment', args=[transaction.id])
                except:
                    pay_url = None
                
                Notification.create_notification(
                    user=client_user,
                    notification_type='request_accepted',
                    title='Request Accepted!',
                    message=f'{request.user.get_full_name()} accepted your request "{req.title}". Please proceed with payment to start work.',
                    request=req,
                    related_user=request.user,
                    link_url=pay_url or f'/requests/{req.id}/'
                )
                
                messages.success(
                    request, 
                    f"✅ Request accepted! Conversation started with {client_user.first_name}. "
                    f"Client will be notified to pay ₱{req.price:,.2f}. You can now message them!"
                )
                
                # Redirect to the conversation so professional can start messaging
                return redirect('messaging:conversation', conversation_id=conversation.id)
                
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                print(f"❌ Error accepting request: {error_detail}")
                messages.error(request, f"Error accepting request: {str(e)}")
                return redirect('professional_requests_list')
        
        elif action == 'decline':
            # Professional declines the request - update status to declined
            req.status = 'declined'
            req.save()
            
            # Notify client
            from analytics.models import Notification
            client_user = CustomUser.objects.filter(email__iexact=req.client).first()
            if client_user:
                Notification.create_notification(
                    user=client_user,
                    notification_type='request_updated',
                    title='Request Declined',
                    message=f'{request.user.get_full_name()} declined your request "{req.title}".',
                    request=req,
                    related_user=request.user,
                    link_url=f'/requests/{req.id}/'
                )
            
            messages.info(request, "Request declined successfully.")
            return redirect('professional_requests_list')
    
    # GET request - show acceptance form
    context = {
        'request': req,
        'user': request.user
    }
    return render(request, 'requests/accept_request.html', context)


# DEPRECATED: Price negotiation removed - client sets price, professional accepts or declines
# def respond_to_price(request, request_id):
#     """This function is no longer used - price negotiation has been simplified"""
#     messages.error(request, "Price negotiation is no longer available.")
#     return redirect('requests_list')
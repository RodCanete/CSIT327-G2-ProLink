from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from supabase import create_client, Client
import json
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
    
    # For now, we'll create some sample data since we don't have real requests yet
    # In a real implementation, you would query the database or Supabase
    sample_requests = [
        {
            'id': 1,
            'title': 'Research Paper Review',
            'description': 'Need expert review of my academic research paper on machine learning applications in healthcare.',
            'professional': 'Dr. Sarah Johnson',
            'status': 'in_progress',
            'price': 75.00,
            'timeline_days': 5,
            'created_at': '2024-01-15',
            'updated_at': '2024-01-17',
            'progress': 60
        },
        {
            'id': 2,
            'title': 'Website Design Consultation',
            'description': 'Looking for professional feedback on my portfolio website design and user experience.',
            'professional': 'Alex Rodriguez',
            'status': 'completed',
            'price': 120.00,
            'timeline_days': 3,
            'created_at': '2024-01-10',
            'updated_at': '2024-01-13',
            'progress': 100
        },
        {
            'id': 3,
            'title': 'Business Plan Review',
            'description': 'Need validation of my startup business plan before presenting to investors.',
            'professional': '',
            'status': 'pending',
            'price': 200.00,
            'timeline_days': 7,
            'created_at': '2024-01-18',
            'updated_at': '2024-01-18',
            'progress': 0
        }
    ]
    
    # Calculate counts for each status
    all_requests_count = len(sample_requests)
    pending_count = len([req for req in sample_requests if req['status'] == 'pending'])
    in_progress_count = len([req for req in sample_requests if req['status'] == 'in_progress'])
    completed_count = len([req for req in sample_requests if req['status'] == 'completed'])
    cancelled_count = len([req for req in sample_requests if req['status'] == 'cancelled'])
    
    # Apply filters
    filtered_requests = sample_requests
    
    if status_filter != 'all':
        filtered_requests = [req for req in filtered_requests if req['status'] == status_filter]
    
    if search_query:
        filtered_requests = [req for req in filtered_requests 
                           if search_query.lower() in req['title'].lower() 
                           or search_query.lower() in req['professional'].lower()]
    
    context = {
        'requests': filtered_requests,
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
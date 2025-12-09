from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .decorators import admin_required
from users.models import CustomUser, ProfessionalProfile
from requests.models import Request
from transactions.models import Transaction, Dispute, WithdrawalRequest
from analytics.models import Review, Notification
from messaging.models import Conversation, Message


def get_open_disputes_count():
    """Helper function to get count of open disputes"""
    return Dispute.objects.filter(status__in=['open', 'under_review']).count()


def get_pending_withdrawals_count():
    """Helper function to get count of pending withdrawals"""
    return WithdrawalRequest.objects.filter(status='pending').count()


@login_required
@admin_required
def admin_dashboard(request):
    """
    Main admin dashboard with platform statistics and overview
    """
    # Calculate date ranges
    today = timezone.now()
    this_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # User Statistics
    total_users = CustomUser.objects.count()
    new_users_this_month = CustomUser.objects.filter(
        date_joined__gte=this_month_start
    ).count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    users_by_role = CustomUser.objects.values('user_role').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Request Statistics
    total_requests = Request.objects.count()
    active_requests = Request.objects.filter(
        status__in=['pending', 'in_progress', 'under_review', 'revision_requested']
    ).count()
    completed_requests = Request.objects.filter(status='completed').count()
    disputed_requests = Request.objects.filter(status='disputed').count()
    requests_this_month = Request.objects.filter(created_at__gte=this_month_start).count()
    
    # Transaction Statistics
    total_transactions = Transaction.objects.count()
    total_revenue = Transaction.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    platform_fees = Transaction.objects.filter(
        status='completed'
    ).aggregate(total=Sum('platform_fee'))['total'] or 0
    escrowed_amount = Transaction.objects.filter(
        status__in=['escrowed', 'pending_approval', 'disputed']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Professional Statistics
    total_professionals = ProfessionalProfile.objects.count()
    active_professionals = ProfessionalProfile.objects.filter(
        is_available=True, user__is_active=True
    ).count()
    verified_professionals = ProfessionalProfile.objects.filter(is_verified=True).count()
    
    # Review Statistics
    total_reviews = Review.objects.count()
    average_rating = Review.objects.aggregate(
        avg=Avg('rating')
    )['avg'] or 0
    
    # Dispute Statistics
    open_disputes = Dispute.objects.filter(
        status__in=['open', 'under_review']
    ).count()
    resolved_disputes = Dispute.objects.filter(
        status__in=['resolved_client', 'resolved_professional', 'resolved_partial']
    ).count()
    
    # Recent Activity
    recent_requests = Request.objects.select_related(
        'transaction'
    ).order_by('-created_at')[:10]
    
    recent_disputes = Dispute.objects.select_related(
        'transaction', 'opened_by', 'transaction__request'
    ).order_by('-created_at')[:5]
    
    # Pass open disputes count for navbar
    open_disputes_count = open_disputes
    
    # Status breakdown
    request_status_breakdown = Request.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    transaction_status_breakdown = Transaction.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-count')
    
    context = {
        'user': request.user,
        'display_name': request.user.get_full_name() or request.user.username,
        
        # User Stats
        'total_users': total_users,
        'new_users_this_month': new_users_this_month,
        'active_users': active_users,
        'users_by_role': users_by_role,
        
        # Request Stats
        'total_requests': total_requests,
        'active_requests': active_requests,
        'completed_requests': completed_requests,
        'disputed_requests': disputed_requests,
        'requests_this_month': requests_this_month,
        'request_status_breakdown': request_status_breakdown,
        
        # Transaction Stats
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
        'platform_fees': platform_fees,
        'escrowed_amount': escrowed_amount,
        'transaction_status_breakdown': transaction_status_breakdown,
        
        # Professional Stats
        'total_professionals': total_professionals,
        'active_professionals': active_professionals,
        'verified_professionals': verified_professionals,
        
        # Review Stats
        'total_reviews': total_reviews,
        'average_rating': round(average_rating, 2),
        
        # Dispute Stats
        'open_disputes': open_disputes,
        'resolved_disputes': resolved_disputes,
        
        # Recent Activity
        'recent_requests': recent_requests,
        'recent_disputes': recent_disputes,
        'open_disputes_count': open_disputes_count,
        'pending_count': get_pending_withdrawals_count(),
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
@admin_required
def admin_users(request):
    """
    User management page
    """
    search_query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    users = CustomUser.objects.all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(user_role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(users.order_by('-date_joined'), 50)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'users': users_page,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'total_users': users.count(),
        'open_disputes_count': get_open_disputes_count(),
    }
    
    return render(request, 'admin_dashboard/users.html', context)


@login_required
@admin_required
def admin_requests(request):
    """
    Request management page
    """
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '').strip()
    
    requests = Request.objects.select_related('transaction').all()
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    if search_query:
        requests = requests.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(client__icontains=search_query) |
            Q(professional__icontains=search_query)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(requests.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    requests_page = paginator.get_page(page_number)
    
    context = {
        'requests': requests_page,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_requests': requests.count(),
        'open_disputes_count': get_open_disputes_count(),
    }
    
    return render(request, 'admin_dashboard/requests.html', context)


@login_required
@admin_required
def admin_disputes(request):
    """
    Dispute management page
    """
    status_filter = request.GET.get('status', '')
    
    disputes = Dispute.objects.select_related(
        'transaction', 'opened_by', 'resolved_by', 'transaction__request'
    ).all()
    
    if status_filter:
        disputes = disputes.filter(status=status_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(disputes.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    disputes_page = paginator.get_page(page_number)
    
    context = {
        'disputes': disputes_page,
        'status_filter': status_filter,
        'total_disputes': disputes.count(),
        'open_disputes_count': get_open_disputes_count(),
    }
    
    return render(request, 'admin_dashboard/disputes.html', context)


@login_required
@admin_required
def admin_dispute_detail(request, dispute_id):
    """
    View and resolve disputes
    """
    dispute = get_object_or_404(
        Dispute.objects.select_related(
            'transaction', 'opened_by', 'resolved_by',
            'transaction__request', 'transaction__client', 'transaction__professional'
        ),
        id=dispute_id
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        resolution_notes = request.POST.get('resolution_notes', '').strip()
        refund_amount = request.POST.get('refund_amount', '0')
        
        if action == 'resolve':
            if not resolution_notes or len(resolution_notes) < 20:
                messages.error(request, 'Please provide detailed resolution notes (minimum 20 characters).')
                return redirect('admin_dashboard:dispute_detail', dispute_id=dispute_id)
            
            resolution_type = request.POST.get('resolution_type')
            
            try:
                refund_amount = float(refund_amount) if refund_amount else 0
            except ValueError:
                refund_amount = 0
            
            # Update dispute
            dispute.status = resolution_type
            dispute.resolution_notes = resolution_notes
            dispute.refund_amount = refund_amount
            dispute.resolved_by = request.user
            dispute.resolved_at = timezone.now()
            dispute.save()
            
            # Update transaction based on resolution
            transaction = dispute.transaction
            if resolution_type in ['resolved_client', 'resolved_partial']:
                transaction.status = 'refunded'
                transaction.save()
            elif resolution_type == 'resolved_professional':
                transaction.status = 'completed'
                transaction.released_at = timezone.now()
                transaction.save()
            
            # Update request status
            request_obj = transaction.request
            request_obj.status = 'completed'
            if not request_obj.completed_at:
                request_obj.completed_at = timezone.now()
            request_obj.save()
            
            # Notify both client and professional about resolution
            from analytics.models import Notification
            from django.urls import reverse
            
            try:
                dispute_url = reverse('transactions:dispute_detail', args=[dispute.id])
            except:
                dispute_url = f'/transactions/dispute/{dispute.id}/'
            
            # Determine resolution outcome message
            if resolution_type == 'resolved_client':
                outcome = 'in favor of the client'
                client_message = f'The dispute for "{request_obj.title}" has been resolved in your favor. '
                if refund_amount > 0:
                    client_message += f'You will receive a refund of ₱{refund_amount:,.2f}.'
                professional_message = f'The dispute for "{request_obj.title}" has been resolved in favor of the client.'
            elif resolution_type == 'resolved_professional':
                outcome = 'in favor of the professional'
                client_message = f'The dispute for "{request_obj.title}" has been resolved in favor of the professional. Payment has been released.'
                professional_message = f'The dispute for "{request_obj.title}" has been resolved in your favor. Payment has been released to you.'
            elif resolution_type == 'resolved_partial':
                outcome = 'with a partial refund'
                client_message = f'The dispute for "{request_obj.title}" has been resolved with a partial refund of ₱{refund_amount:,.2f}.'
                professional_message = f'The dispute for "{request_obj.title}" has been resolved with a partial refund to the client of ₱{refund_amount:,.2f}.'
            else:
                outcome = 'closed'
                client_message = f'The dispute for "{request_obj.title}" has been closed.'
                professional_message = f'The dispute for "{request_obj.title}" has been closed.'
            
            # Notify Client
            Notification.create_notification(
                user=transaction.client,
                notification_type='dispute_resolved',
                title='Dispute Resolved',
                message=client_message,
                request=request_obj,
                related_user=request.user,
                link_url=dispute_url
            )
            
            # Notify Professional
            Notification.create_notification(
                user=transaction.professional,
                notification_type='dispute_resolved',
                title='Dispute Resolved',
                message=professional_message,
                request=request_obj,
                related_user=request.user,
                link_url=dispute_url
            )
            
            messages.success(request, f'Dispute resolved successfully. Status: {dispute.get_status_display()}. Both parties have been notified.')
            return redirect('admin_dashboard:disputes')
    
    # Parse file attachments
    import json
    request_obj = dispute.transaction.request
    
    # Parse original request attachments
    attached_files = []
    if request_obj.attached_files:
        try:
            attached_files = json.loads(request_obj.attached_files)
        except json.JSONDecodeError:
            attached_files = []
    
    # Parse deliverable files (work submitted by professional)
    deliverable_files = []
    if hasattr(request_obj, 'deliverable_files') and request_obj.deliverable_files:
        try:
            deliverable_files = json.loads(request_obj.deliverable_files)
        except json.JSONDecodeError:
            deliverable_files = []
    
    # Parse dispute evidence files
    client_evidence_files = []
    if dispute.client_files:
        try:
            client_evidence_files = json.loads(dispute.client_files)
        except json.JSONDecodeError:
            client_evidence_files = []
    
    professional_evidence_files = []
    if dispute.professional_files:
        try:
            professional_evidence_files = json.loads(dispute.professional_files)
        except json.JSONDecodeError:
            professional_evidence_files = []
    
    context = {
        'dispute': dispute,
        'transaction': dispute.transaction,
        'request_obj': request_obj,
        'attached_files': attached_files,
        'deliverable_files': deliverable_files,
        'client_evidence_files': client_evidence_files,
        'professional_evidence_files': professional_evidence_files,
        'open_disputes_count': get_open_disputes_count(),
    }
    
    return render(request, 'admin_dashboard/dispute_detail.html', context)


@login_required
@admin_required
def admin_transactions(request):
    """
    Transaction management page
    """
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '').strip()
    
    transactions = Transaction.objects.select_related(
        'request', 'client', 'professional'
    ).all()
    
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    if search_query:
        transactions = transactions.filter(
            Q(id__icontains=search_query) |
            Q(request__title__icontains=search_query) |
            Q(client__email__icontains=search_query) |
            Q(professional__email__icontains=search_query)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transactions.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    transactions_page = paginator.get_page(page_number)
    
    context = {
        'transactions': transactions_page,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_transactions': transactions.count(),
        'open_disputes_count': get_open_disputes_count(),
    }
    
    return render(request, 'admin_dashboard/transactions.html', context)


@login_required
@admin_required
def admin_professionals(request):
    """
    Professional management page
    """
    search_query = request.GET.get('q', '').strip()
    verified_filter = request.GET.get('verified', '')
    available_filter = request.GET.get('available', '')
    
    professionals = ProfessionalProfile.objects.select_related('user').all()
    
    if search_query:
        professionals = professionals.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    if verified_filter == 'verified':
        professionals = professionals.filter(is_verified=True)
    elif verified_filter == 'unverified':
        professionals = professionals.filter(is_verified=False)
    
    if available_filter == 'available':
        professionals = professionals.filter(is_available=True)
    elif available_filter == 'unavailable':
        professionals = professionals.filter(is_available=False)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(professionals.order_by('-average_rating'), 25)
    page_number = request.GET.get('page')
    professionals_page = paginator.get_page(page_number)
    
    context = {
        'professionals': professionals_page,
        'search_query': search_query,
        'verified_filter': verified_filter,
        'available_filter': available_filter,
        'total_professionals': professionals.count(),
        'open_disputes_count': get_open_disputes_count(),
    }
    
    return render(request, 'admin_dashboard/professionals.html', context)


@login_required
@admin_required
def toggle_user_status(request, user_id):
    """
    Toggle user active/inactive status
    """
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} has been {status}.')
    
    return redirect('admin_dashboard:users')


@login_required
@admin_required
def toggle_professional_verification(request, professional_id):
    """
    Toggle professional verification status
    """
    if request.method == 'POST':
        professional = get_object_or_404(ProfessionalProfile, id=professional_id)
        professional.is_verified = not professional.is_verified
        professional.save()
        
        status = 'verified' if professional.is_verified else 'unverified'
        messages.success(request, f'Professional {professional.user.username} has been {status}.')
    
    return redirect('admin_dashboard:professionals')


@login_required
@admin_required
def withdrawal_requests(request):
    """
    View and manage withdrawal requests from professionals
    """
    # Get filter parameters
    status_filter = request.GET.get('status', 'pending')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    withdrawals = WithdrawalRequest.objects.select_related('professional', 'processed_by')
    
    # Apply status filter
    if status_filter and status_filter != 'all':
        withdrawals = withdrawals.filter(status=status_filter)
    
    # Apply search
    if search_query:
        withdrawals = withdrawals.filter(
            Q(professional__username__icontains=search_query) |
            Q(professional__email__icontains=search_query) |
            Q(gcash_number__icontains=search_query) |
            Q(bank_account_number__icontains=search_query)
        )
    
    # Order by date (newest first)
    withdrawals = withdrawals.order_by('-created_at')
    
    # Calculate statistics
    pending_count = WithdrawalRequest.objects.filter(status='pending').count()
    processing_count = WithdrawalRequest.objects.filter(status='processing').count()
    total_pending_amount = WithdrawalRequest.objects.filter(
        status__in=['pending', 'processing']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'withdrawals': withdrawals,
        'status_filter': status_filter,
        'search_query': search_query,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'total_pending_amount': total_pending_amount,
        'open_disputes_count': get_open_disputes_count(),
    }
    
    return render(request, 'admin_dashboard/withdrawal_requests.html', context)


@login_required
@admin_required
def approve_withdrawal(request, withdrawal_id):
    """
    Approve and complete a withdrawal request
    """
    if request.method == 'POST':
        withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
        
        # Check if already processed
        if withdrawal.status == 'completed':
            messages.warning(request, 'This withdrawal has already been completed.')
            return redirect('admin_dashboard:withdrawal_requests')
        
        # Get admin notes from form
        admin_notes = request.POST.get('admin_notes', '')
        
        # Update withdrawal
        withdrawal.status = 'completed'
        withdrawal.processed_by = request.user
        withdrawal.processed_at = timezone.now()
        withdrawal.admin_notes = admin_notes
        withdrawal.save()
        
        # Send notification to professional
        try:
            Notification.create_notification(
                user=withdrawal.professional,
                notification_type='payment_released',
                title='Withdrawal Completed',
                message=f'Your withdrawal request for ₱{withdrawal.amount:,.2f} has been processed and completed.',
                link_url='/earnings/'
            )
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        messages.success(request, f'Withdrawal of ₱{withdrawal.amount:,.2f} to {withdrawal.professional.username} has been approved and completed.')
        return redirect('admin_dashboard:withdrawal_requests')
    
    return redirect('admin_dashboard:withdrawal_requests')


@login_required
@admin_required
def reject_withdrawal(request, withdrawal_id):
    """
    Reject/cancel a withdrawal request
    """
    if request.method == 'POST':
        withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
        
        # Check if already processed
        if withdrawal.status in ['completed', 'cancelled']:
            messages.warning(request, 'This withdrawal has already been processed.')
            return redirect('admin_dashboard:withdrawal_requests')
        
        # Get rejection reason
        admin_notes = request.POST.get('admin_notes', '')
        
        # Update withdrawal
        withdrawal.status = 'cancelled'
        withdrawal.processed_by = request.user
        withdrawal.processed_at = timezone.now()
        withdrawal.admin_notes = admin_notes
        withdrawal.save()
        
        # Send notification to professional
        try:
            Notification.create_notification(
                user=withdrawal.professional,
                notification_type='general',
                title='Withdrawal Request Cancelled',
                message=f'Your withdrawal request for ₱{withdrawal.amount:,.2f} has been cancelled. Reason: {admin_notes}',
                link_url='/earnings/'
            )
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        messages.warning(request, f'Withdrawal of ₱{withdrawal.amount:,.2f} to {withdrawal.professional.username} has been cancelled.')
        return redirect('admin_dashboard:withdrawal_requests')
    
    return redirect('admin_dashboard:withdrawal_requests')


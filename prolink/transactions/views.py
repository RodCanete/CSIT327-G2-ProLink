from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import Transaction, Dispute
from requests.models import Request
from users.models import CustomUser
import json


# ============= PAYMENT FLOW =============

@login_required
def create_payment(request, request_id):
    """Client submits GCash payment proof"""
    from django.conf import settings
    
    service_request = get_object_or_404(Request, id=request_id)
    
    # Ensure user is the client
    if request.user.email != service_request.client:
        messages.error(request, 'You do not have permission to pay for this request.')
        return redirect('dashboard')
    
    # Get transaction
    try:
        transaction = Transaction.objects.get(request=service_request)
    except Transaction.DoesNotExist:
        messages.error(request, 'No transaction found for this request.')
        return redirect('dashboard')
    
    if transaction.status != 'pending_payment':
        messages.info(request, 'Payment has already been submitted.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        gcash_number = request.POST.get('gcash_number')
        gcash_reference = request.POST.get('gcash_reference')
        screenshot = request.FILES.get('gcash_screenshot')
        
        if not all([gcash_number, gcash_reference, screenshot]):
            messages.error(request, 'Please provide all required payment information.')
            return render(request, 'transactions/create_payment.html', {
                'service_request': service_request,
                'transaction': transaction,
                'prolink_gcash_number': settings.PROLINK_GCASH_NUMBER,
                'prolink_gcash_name': settings.PROLINK_GCASH_NAME,
            })
        
        try:
            # Upload screenshot to Supabase
            from requests.storage_utils import upload_to_supabase
            screenshot_url = upload_to_supabase(screenshot, f'payment_proofs/{transaction.id}_{screenshot.name}')
            
            # Update transaction
            transaction.gcash_number = gcash_number
            transaction.transaction_id = gcash_reference
            transaction.gcash_screenshot = screenshot_url
            transaction.status = 'escrowed'  # Auto-approve for MVP
            transaction.paid_at = timezone.now()
            transaction.save()
            
            # Update request status
            service_request.status = 'in_progress'
            service_request.save()
            
            messages.success(request, f'Payment submitted successfully! The professional has been notified.')
            return redirect('transactions:payment_success', transaction_id=transaction.id)
            
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    context = {
        'service_request': service_request,
        'transaction': transaction,
        'prolink_gcash_number': settings.PROLINK_GCASH_NUMBER,
        'prolink_gcash_name': settings.PROLINK_GCASH_NAME,
    }
    return render(request, 'transactions/create_payment.html', context)


@login_required
def payment_success(request, transaction_id):
    """Payment confirmation page"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    return render(request, 'transactions/payment_success.html', {'transaction': transaction})


# ============= WORK SUBMISSION & APPROVAL =============

@login_required
def submit_work(request, request_id):
    """Professional submits deliverables"""
    service_request = get_object_or_404(Request, id=request_id)
    
    # Debug logging
    print(f"=== SUBMIT WORK VIEW ===")
    print(f"Request ID: {request_id}")
    print(f"User email: {request.user.email}")
    print(f"Professional email: {service_request.professional}")
    print(f"Request status: {service_request.status}")
    
    # Ensure user is the professional
    if request.user.email != service_request.professional:
        print(f"ERROR: User not professional")
        messages.error(request, 'You do not have permission to submit work for this request.')
        return redirect('dashboard')
    
    # Ensure request is in progress (or allow revision_requested status)
    if service_request.status not in ['in_progress', 'revision_requested']:
        print(f"ERROR: Invalid status: {service_request.status}")
        messages.error(request, f'This request is not ready for submission. Current status: {service_request.get_status_display()}')
        messages.warning(request, f'Request must be "In Progress" or "Revision Requested". Current: {service_request.status}')
        return redirect('dashboard')
    
    # Get or create transaction
    try:
        transaction = Transaction.objects.get(request=service_request)
        print(f"Transaction found: ID={transaction.id}, Status={transaction.status}")
    except Transaction.DoesNotExist:
        print(f"ERROR: No transaction found")
        messages.error(request, 'No transaction found for this request. Please contact support.')
        return redirect('dashboard')
    
    # Ensure payment is escrowed (allow pending_approval for resubmissions)
    if transaction.status not in ['escrowed', 'pending_approval']:
        print(f"ERROR: Invalid transaction status: {transaction.status}")
        messages.error(request, f'Payment must be escrowed before submitting work. Current payment status: {transaction.get_status_display()}')
        messages.warning(request, f'Transaction status must be "Escrowed" or "Pending Approval". Current: {transaction.status}')
        return redirect('dashboard')
    
    if request.method == 'POST':
        print("=== SUBMIT WORK POST REQUEST ===")
        deliverable_notes = request.POST.get('deliverable_notes', '').strip()
        deliverable_files = request.FILES.getlist('deliverable_files')
        print(f"Notes: {deliverable_notes[:50] if deliverable_notes else 'None'}...")
        print(f"Files: {len(deliverable_files)} files uploaded")
        
        if not deliverable_notes:
            messages.error(request, 'Please provide notes about your deliverables.')
            return render(request, 'transactions/submit_work.html', {
                'service_request': service_request,
                'transaction': transaction,
            })
        
        if not deliverable_files:
            messages.error(request, 'Please upload at least one deliverable file.')
            return render(request, 'transactions/submit_work.html', {
                'service_request': service_request,
                'transaction': transaction,
            })
        
        try:
            # Upload files to Supabase
            from requests.storage_utils import upload_to_supabase
            uploaded_files = []
            
            for file in deliverable_files:
                file_url = upload_to_supabase(file, f'deliverables/{service_request.id}_{file.name}')
                uploaded_files.append({
                    'name': file.name,
                    'url': file_url,
                    'size': file.size
                })
            
            # Update request
            service_request.deliverable_files = json.dumps(uploaded_files)
            service_request.deliverable_notes = deliverable_notes
            service_request.status = 'under_review'
            service_request.submitted_at = timezone.now()
            service_request.save()
            
            # Update transaction
            transaction.status = 'pending_approval'
            transaction.save()
            
            messages.success(request, 'Work submitted successfully! The client will review and approve.')
            return redirect('transactions:submission_success', request_id=service_request.id)
            
        except Exception as e:
            messages.error(request, f'Error submitting work: {str(e)}')
            return render(request, 'transactions/submit_work.html', {
                'service_request': service_request,
                'transaction': transaction,
            })
    
    context = {
        'service_request': service_request,
        'transaction': transaction,
    }
    return render(request, 'transactions/submit_work.html', context)


@login_required
def submission_success(request, request_id):
    """Work submission success page"""
    service_request = get_object_or_404(Request, id=request_id)
    transaction = get_object_or_404(Transaction, request=service_request)
    
    context = {
        'service_request': service_request,
        'transaction': transaction,
    }
    return render(request, 'transactions/submission_success.html', context)


@login_required
def approve_work(request, request_id):
    """Client approves work and releases payment"""
    service_request = get_object_or_404(Request, id=request_id)
    
    # Ensure user is the client
    if request.user.email != service_request.client:
        messages.error(request, 'You do not have permission to approve this work.')
        return redirect('dashboard')
    
    # Ensure work is submitted
    if service_request.status != 'under_review':
        messages.error(request, 'Work has not been submitted yet.')
        return redirect('dashboard')
    
    # Get transaction
    try:
        transaction = Transaction.objects.get(request=service_request)
    except Transaction.DoesNotExist:
        messages.error(request, 'No transaction found.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            # Update request status
            service_request.status = 'completed'
            service_request.completed_at = timezone.now()
            service_request.save()
            
            # Release payment
            transaction.status = 'completed'
            transaction.released_at = timezone.now()
            transaction.save()
            
            messages.success(request, f'Work approved! Payment of ₱{transaction.professional_payout:,.2f} has been released to the professional.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error approving work: {str(e)}')
    
    return redirect('dashboard')


@login_required
def request_revision(request, request_id):
    """Client requests revision to submitted work"""
    service_request = get_object_or_404(Request, id=request_id)
    
    # Ensure user is the client
    if request.user.email != service_request.client:
        messages.error(request, 'You do not have permission to request revision.')
        return redirect('dashboard')
    
    # Ensure work is submitted
    if service_request.status != 'under_review':
        messages.error(request, 'Work has not been submitted yet.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        revision_notes = request.POST.get('revision_notes', '').strip()
        
        if not revision_notes:
            messages.error(request, 'Please provide revision instructions.')
            return redirect('dashboard')
        
        try:
            # Get transaction
            transaction = Transaction.objects.get(request=service_request)
            
            # Update request
            service_request.status = 'revision_requested'
            service_request.revision_notes = revision_notes
            service_request.save()
            
            # Transaction stays in pending_approval
            
            messages.success(request, 'Revision requested! The professional has been notified.')
            return redirect('messaging:inbox')
            
        except Transaction.DoesNotExist:
            messages.error(request, 'No transaction found.')
        except Exception as e:
            messages.error(request, f'Error requesting revision: {str(e)}')
    
    return redirect('dashboard')


# ============= DISPUTE MANAGEMENT =============

@login_required
def open_dispute(request, transaction_id):
    """Open a dispute for a transaction"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.method == 'POST':
        # TODO: Implement dispute creation
        messages.success(request, 'Dispute system coming soon!')
        return redirect('transactions:detail', transaction_id=transaction_id)
    
    return render(request, 'transactions/open_dispute.html', {'transaction': transaction})


@login_required
def dispute_detail(request, dispute_id):
    """View dispute details"""
    dispute = get_object_or_404(Dispute, id=dispute_id)
    return render(request, 'transactions/dispute_detail.html', {'dispute': dispute})


@login_required
def submit_evidence(request, dispute_id):
    """Submit evidence for a dispute"""
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    if request.method == 'POST':
        # TODO: Implement evidence submission
        messages.success(request, 'Evidence submission coming soon!')
        return redirect('transactions:dispute_detail', dispute_id=dispute_id)
    
    return redirect('transactions:dispute_detail', dispute_id=dispute_id)


# ============= TRANSACTION HISTORY =============

@login_required
def transaction_history(request):
    """View all user's transactions"""
    user = request.user
    
    if user.user_role == 'professional':
        transactions = Transaction.objects.filter(professional=user)
    else:
        transactions = Transaction.objects.filter(client=user)
    
    return render(request, 'transactions/history.html', {'transactions': transactions})


@login_required
def transaction_detail(request, transaction_id):
    """View detailed transaction information"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Ensure user is involved in this transaction
    if request.user not in [transaction.client, transaction.professional]:
        messages.error(request, 'You do not have permission to view this transaction.')
        return redirect('dashboard')
    
    return render(request, 'transactions/detail.html', {'transaction': transaction})

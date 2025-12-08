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
            # Upload files to Supabase (deliverables folder, separate from request-files roots)
            from requests.storage_utils import get_storage_manager
            storage_manager = get_storage_manager()
            uploaded_files = []
            
            for file in deliverable_files:
                info = storage_manager.upload_file(file, folder=f'deliverables/{service_request.id}')
                uploaded_files.append({
                    'name': info.get('original_name', file.name),
                    'url': info.get('public_url'),
                    'size': info.get('size')
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
            
            # Notify client that work has been submitted
            from analytics.models import Notification
            from django.urls import reverse
            from users.models import CustomUser
            
            client_user = CustomUser.objects.filter(email__iexact=service_request.client).first()
            if client_user:
                try:
                    review_url = reverse('request_detail', args=[service_request.id])
                except:
                    review_url = f'/requests/{service_request.id}/'
                
                Notification.create_notification(
                    user=client_user,
                    notification_type='work_submitted',
                    title='Work Submitted for Review',
                    message=f'{request.user.get_full_name()} has submitted work for "{service_request.title}". Please review and approve.',
                    request=service_request,
                    related_user=request.user,
                    link_url=review_url
                )
            
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
        messages.error(request, f'Cannot approve work. Current status: {service_request.get_status_display()}')
        return redirect('request_detail', request_id=request_id)
    
    # Get transaction
    try:
        transaction = Transaction.objects.get(request=service_request)
    except Transaction.DoesNotExist:
        messages.error(request, 'No transaction found.')
        return redirect('dashboard')
    
    # Ensure transaction is pending approval
    if transaction.status != 'pending_approval':
        messages.error(request, f'Payment cannot be released. Transaction status: {transaction.get_status_display()}')
        return redirect('request_detail', request_id=request_id)
    
    if request.method == 'POST':
        try:
            # Update request status
            service_request.status = 'completed'
            service_request.completed_at = timezone.now()
            service_request.auto_approve_date = None  # Clear auto-approve
            service_request.save()
            
            # Release payment
            transaction.status = 'completed'
            transaction.released_at = timezone.now()
            transaction.save()
            
            # Notify professional that work was approved and payment released
            from analytics.models import Notification
            from django.urls import reverse
            from users.models import CustomUser
            
            professional_user = CustomUser.objects.filter(email__iexact=service_request.professional).first()
            if professional_user:
                try:
                    request_url = reverse('professional_request_detail', args=[service_request.id])
                except:
                    request_url = f'/requests/professional/{service_request.id}/'
                
                Notification.create_notification(
                    user=professional_user,
                    notification_type='work_approved',
                    title='Work Approved! Payment Released',
                    message=f'Your work for "{service_request.title}" has been approved! Payment of ₱{transaction.professional_payout:,.2f} has been released to you.',
                    request=service_request,
                    related_user=request.user,
                    link_url=request_url
                )
            
            messages.success(request, f'✅ Work approved! Payment of ₱{transaction.professional_payout:,.2f} has been released to {service_request.professional}.')
            return redirect('request_detail', request_id=request_id)
            
        except Exception as e:
            messages.error(request, f'Error approving work: {str(e)}')
            return redirect('request_detail', request_id=request_id)
    
    # GET request - show confirmation page
    context = {
        'service_request': service_request,
        'transaction': transaction,
    }
    return render(request, 'transactions/approve_work.html', context)


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
        messages.error(request, f'Cannot request revision. Current status: {service_request.get_status_display()}')
        return redirect('request_detail', request_id=request_id)
    
    # Check revision limit
    if service_request.revision_count >= service_request.max_revisions:
        messages.error(request, 
            f'Maximum revisions ({service_request.max_revisions}) reached. '
            'You must either approve the work or open a dispute.'
        )
        return redirect('request_detail', request_id=request_id)
    
    if request.method == 'POST':
        revision_notes = request.POST.get('revision_notes', '').strip()
        
        if not revision_notes or len(revision_notes) < 20:
            messages.error(request, 'Please provide detailed revision instructions (minimum 20 characters).')
            context = {
                'service_request': service_request,
                'remaining_revisions': service_request.max_revisions - service_request.revision_count,
            }
            return render(request, 'transactions/request_revision.html', context)
        
        try:
            # Get transaction (just for validation)
            Transaction.objects.get(request=service_request)
            
            # Update request
            service_request.status = 'revision_requested'
            service_request.revision_notes = revision_notes
            service_request.revision_count += 1  # Increment revision counter
            service_request.auto_approve_date = None  # Reset auto-approve timer
            service_request.save()
            
            # Transaction stays in 'pending_approval' - money still in escrow
            
            # Notify professional that revision was requested
            from analytics.models import Notification
            from django.urls import reverse
            from users.models import CustomUser
            
            professional_user = CustomUser.objects.filter(email__iexact=service_request.professional).first()
            if professional_user:
                try:
                    request_url = reverse('professional_request_detail', args=[service_request.id])
                except:
                    request_url = f'/requests/professional/{service_request.id}/'
                
                revisions_left = service_request.max_revisions - service_request.revision_count
                Notification.create_notification(
                    user=professional_user,
                    notification_type='revision_requested',
                    title='Revision Requested',
                    message=f'Client requested a revision for "{service_request.title}". {revisions_left} revision{"s" if revisions_left != 1 else ""} remaining.',
                    request=service_request,
                    related_user=request.user,
                    link_url=request_url
                )
            
            revisions_left = service_request.max_revisions - service_request.revision_count
            
            messages.success(request, 
                f'✅ Revision requested! ({service_request.revision_count}/{service_request.max_revisions} used) '
                f'The professional has been notified. {revisions_left} revision(s) remaining.'
            )
            return redirect('request_detail', request_id=request_id)
            
        except Transaction.DoesNotExist:
            messages.error(request, 'No transaction found.')
            return redirect('dashboard')
    
    # GET request - show revision request form
    context = {
        'service_request': service_request,
        'remaining_revisions': service_request.max_revisions - service_request.revision_count,
    }
    return render(request, 'transactions/request_revision.html', context)


# ============= DISPUTE MANAGEMENT =============

@login_required
def open_dispute(request, request_id):
    """Client opens a dispute for a request"""
    service_request = get_object_or_404(Request, id=request_id)
    
    # Ensure user is the client
    if request.user.email != service_request.client:
        messages.error(request, 'Only the client can open a dispute.')
        return redirect('dashboard')
    
    # Get transaction
    try:
        transaction = Transaction.objects.get(request=service_request)
    except Transaction.DoesNotExist:
        messages.error(request, 'No transaction found for this request.')
        return redirect('dashboard')
    
    # Check if dispute can be opened
    if transaction.status not in ['escrowed', 'pending_approval']:
        messages.error(request, 
            f'Cannot open dispute. Transaction must be in escrow or pending approval. '
            f'Current status: {transaction.get_status_display()}'
        )
        return redirect('request_detail', request_id=request_id)
    
    # Check if dispute already exists
    if hasattr(transaction, 'dispute'):
        messages.warning(request, 'A dispute has already been opened for this transaction.')
        return redirect('transactions:dispute_detail', dispute_id=transaction.dispute.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        client_evidence = request.POST.get('client_evidence', '').strip()
        evidence_files = request.FILES.getlist('evidence_files')
        
        # Validation
        if not reason or len(reason) < 50:
            messages.error(request, 'Please provide a detailed reason for the dispute (minimum 50 characters).')
            context = {
                'service_request': service_request,
                'transaction': transaction,
            }
            return render(request, 'transactions/open_dispute.html', context)
        
        try:
            # Upload evidence files
            uploaded_evidence = []
            if evidence_files:
                from requests.storage_utils import get_storage_manager
                storage_manager = get_storage_manager()
                for file in evidence_files:
                    result = storage_manager.upload_file(file, folder=f'disputes/{transaction.id}')
                    if result.get('success'):
                        uploaded_evidence.append({
                            'name': file.name,
                            'url': result.get('url'),
                            'size': file.size
                        })
            
            # Create dispute
            dispute = Dispute.objects.create(
                transaction=transaction,
                opened_by=request.user,
                reason=reason,
                client_evidence=client_evidence,
                client_files=json.dumps(uploaded_evidence),
                status='open'
            )
            
            # Update transaction status
            transaction.status = 'disputed'
            transaction.save()
            
            # Update request status
            service_request.status = 'disputed'
            service_request.save()
            
            # Notify professional about the dispute
            from analytics.models import Notification
            from django.urls import reverse
            from users.models import CustomUser
            
            professional_user = CustomUser.objects.filter(email__iexact=service_request.professional).first()
            if professional_user:
                try:
                    dispute_url = reverse('transactions:dispute_detail', args=[dispute.id])
                except:
                    dispute_url = f'/transactions/dispute/{dispute.id}/'
                
                Notification.create_notification(
                    user=professional_user,
                    notification_type='dispute_opened',
                    title='Dispute Opened',
                    message=f'A dispute has been opened for "{service_request.title}". Please respond with your evidence.',
                    request=service_request,
                    related_user=request.user,
                    link_url=dispute_url
                )
            
            # Notify all admins about the dispute
            admin_users = CustomUser.objects.filter(is_staff=True, is_superuser=True)
            for admin in admin_users:
                try:
                    dispute_url = reverse('transactions:dispute_detail', args=[dispute.id])
                except:
                    dispute_url = f'/transactions/dispute/{dispute.id}/'
                
                Notification.create_notification(
                    user=admin,
                    notification_type='dispute_admin_review',
                    title='New Dispute Requires Review',
                    message=f'A dispute has been opened for "{service_request.title}" (Transaction #{transaction.id}). Client: {request.user.get_full_name() or request.user.email}',
                    request=service_request,
                    related_user=request.user,
                    link_url=dispute_url
                )
            
            messages.success(request, 
                '⚠️ Dispute opened successfully. An administrator will review your case within 24-48 hours. '
                'Transaction funds are now frozen.'
            )
            return redirect('transactions:dispute_submitted', dispute_id=dispute.id)
            
        except Exception as e:
            messages.error(request, f'Error opening dispute: {str(e)}')
            return redirect('request_detail', request_id=request_id)
    
    # GET request - show dispute form
    context = {
        'service_request': service_request,
        'transaction': transaction,
    }
    return render(request, 'transactions/open_dispute.html', context)


@login_required
def dispute_submitted(request, dispute_id):
    """Dispute submission confirmation page"""
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    # Ensure user is the one who opened the dispute
    if request.user != dispute.opened_by:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    context = {
        'dispute': dispute,
    }
    return render(request, 'transactions/dispute_submitted.html', context)


@login_required
def dispute_detail(request, dispute_id):
    """View dispute details"""
    dispute = get_object_or_404(Dispute, id=dispute_id)
    transaction = dispute.transaction
    service_request = transaction.request
    
    # Ensure user is involved or is admin
    is_involved = request.user in [transaction.client, transaction.professional]
    is_admin = request.user.is_staff or request.user.is_superuser
    
    if not (is_involved or is_admin):
        messages.error(request, 'You do not have permission to view this dispute.')
        return redirect('dashboard')
    
    # Parse evidence files
    client_files = []
    professional_files = []
    
    if dispute.client_files:
        try:
            client_files = json.loads(dispute.client_files)
        except json.JSONDecodeError:
            client_files = []
    
    if dispute.professional_files:
        try:
            professional_files = json.loads(dispute.professional_files)
        except json.JSONDecodeError:
            professional_files = []
    
    context = {
        'dispute': dispute,
        'transaction': transaction,
        'service_request': service_request,
        'client_files': client_files,
        'professional_files': professional_files,
        'is_admin': is_admin,
        'is_client': request.user == transaction.client,
        'is_professional': request.user == transaction.professional,
    }
    return render(request, 'transactions/dispute_detail.html', context)


@login_required
def submit_evidence(request, dispute_id):
    """Submit evidence for a dispute (Professional only)"""
    dispute = get_object_or_404(Dispute, id=dispute_id)
    transaction = dispute.transaction
    
    # Ensure user is the professional
    if request.user != transaction.professional:
        messages.error(request, 'Only the professional can submit counter-evidence.')
        return redirect('transactions:dispute_detail', dispute_id=dispute_id)
    
    # Ensure dispute is open or under review
    if dispute.status not in ['open', 'under_review']:
        messages.error(request, f'Cannot submit evidence. Dispute status: {dispute.get_status_display()}')
        return redirect('transactions:dispute_detail', dispute_id=dispute_id)
    
    if request.method == 'POST':
        professional_evidence = request.POST.get('professional_evidence', '').strip()
        evidence_files = request.FILES.getlist('evidence_files')
        
        if not professional_evidence or len(professional_evidence) < 50:
            messages.error(request, 'Please provide detailed evidence (minimum 50 characters).')
            return redirect('transactions:dispute_detail', dispute_id=dispute_id)
        
        try:
            # Upload evidence files
            uploaded_evidence = []
            if evidence_files:
                from requests.storage_utils import get_storage_manager
                storage_manager = get_storage_manager()
                for file in evidence_files:
                    result = storage_manager.upload_file(file, folder=f'disputes/{transaction.id}')
                    if result.get('success'):
                        uploaded_evidence.append({
                            'name': file.name,
                            'url': result.get('url'),
                            'size': file.size
                        })
            
            # Update dispute
            dispute.professional_evidence = professional_evidence
            dispute.professional_files = json.dumps(uploaded_evidence)
            dispute.status = 'under_review'  # Move to under_review once professional responds
            dispute.save()
            
            messages.success(request, '✅ Evidence submitted successfully. Admin will review both sides.')
            return redirect('transactions:dispute_detail', dispute_id=dispute_id)
            
        except Exception as e:
            messages.error(request, f'Error submitting evidence: {str(e)}')
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
    
    # Parse deliverable files (submitted by professional)
    deliverable_files = []
    if getattr(transaction.request, 'deliverable_files', None):
        try:
            deliverable_files = json.loads(transaction.request.deliverable_files)
        except (json.JSONDecodeError, TypeError):
            # Handle legacy format where it might be a single URL string
            if isinstance(transaction.request.deliverable_files, str):
                deliverable_files = [{'url': transaction.request.deliverable_files}]
            else:
                deliverable_files = []
    
    context = {
        'transaction': transaction,
        'deliverable_files': deliverable_files,
    }
    
    return render(request, 'transactions/detail.html', context)

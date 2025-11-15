from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .models import Transaction
from .paymongo_service import PayMongoService
import json


@login_required
def initiate_payment(request, transaction_id):
    """Client initiates payment for a transaction"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Verify client owns this transaction
    if request.user != transaction.client:
        messages.error(request, "You don't have permission to pay for this transaction.")
        return redirect('dashboard')
    
    # Check if already paid
    if transaction.status != 'pending_payment':
        messages.info(request, "This transaction has already been processed.")
        return redirect('transactions:detail', transaction_id=transaction.id)
    
    # Initialize PayMongo service
    paymongo = PayMongoService()
    
    # Build URLs
    success_url = request.build_absolute_uri(f'/transactions/{transaction.id}/payment-success/')
    cancel_url = request.build_absolute_uri(f'/transactions/{transaction.id}/payment-cancel/')
    
    # Create checkout session
    result = paymongo.create_checkout_session(
        transaction=transaction,
        success_url=success_url,
        cancel_url=cancel_url
    )
    
    if result['success']:
        # Store checkout ID in transaction for later verification
        transaction.transaction_id = result['checkout_id']
        transaction.save()
        
        # Redirect to PayMongo checkout page
        return redirect(result['checkout_url'])
    else:
        messages.error(request, f"Failed to create payment session: {result.get('message', 'Unknown error')}")
        return redirect('dashboard')


@login_required
def payment_success(request, transaction_id):
    """Handle successful payment callback"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Verify user owns this transaction
    if request.user != transaction.client:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
    
    # Initialize PayMongo service
    paymongo = PayMongoService()
    
    # Verify payment status
    if transaction.transaction_id:
        payment_status = paymongo.get_payment_status(transaction.transaction_id)
        
        if payment_status == 'paid':
            # Update transaction status
            transaction.status = 'escrowed'
            transaction.payment_method = 'paymongo'
            transaction.save()
            
            # Update request status
            transaction.request.status = 'in_progress'
            transaction.request.save()
            
            messages.success(request, f"Payment successful! ₱{transaction.amount:,.2f} has been escrowed. Professional can now start work.")
        else:
            messages.warning(request, "Payment verification pending. Please wait a moment and refresh.")
    
    context = {
        'transaction': transaction,
        'request': transaction.request,
        'professional': transaction.professional,
        'test_mode': settings.PAYMONGO_TEST_MODE
    }
    
    return render(request, 'transactions/payment_success.html', context)


@login_required
def payment_cancel(request, transaction_id):
    """Handle cancelled payment"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Verify user owns this transaction
    if request.user != transaction.client:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
    
    messages.info(request, "Payment was cancelled. You can try again when ready.")
    
    context = {
        'transaction': transaction,
        'request': transaction.request
    }
    
    return render(request, 'transactions/payment_cancel.html', context)


@csrf_exempt
def paymongo_webhook(request):
    """Handle PayMongo webhook events"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # Get webhook data
        payload = json.loads(request.body)
        event_type = payload.get('data', {}).get('attributes', {}).get('type')
        
        # Initialize PayMongo service
        paymongo = PayMongoService()
        
        # Verify webhook signature (implement in production)
        # signature = request.headers.get('paymongo-signature')
        # if not paymongo.verify_webhook_signature(request.body, signature):
        #     return HttpResponse(status=401)
        
        # Handle different event types
        if event_type == 'payment.paid':
            # Payment successful
            checkout_id = payload.get('data', {}).get('attributes', {}).get('data', {}).get('id')
            metadata = payload.get('data', {}).get('attributes', {}).get('data', {}).get('attributes', {}).get('metadata', {})
            transaction_id = metadata.get('transaction_id')
            
            if transaction_id:
                try:
                    transaction = Transaction.objects.get(id=transaction_id)
                    transaction.status = 'escrowed'
                    transaction.save()
                    
                    # Update request status
                    transaction.request.status = 'in_progress'
                    transaction.request.save()
                except Transaction.DoesNotExist:
                    pass
        
        elif event_type == 'payment.failed':
            # Payment failed
            metadata = payload.get('data', {}).get('attributes', {}).get('data', {}).get('attributes', {}).get('metadata', {})
            transaction_id = metadata.get('transaction_id')
            
            if transaction_id:
                try:
                    transaction = Transaction.objects.get(id=transaction_id)
                    transaction.status = 'failed'
                    transaction.save()
                except Transaction.DoesNotExist:
                    pass
        
        return HttpResponse(status=200)
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return HttpResponse(status=500)


@login_required
def test_payment_info(request):
    """Show test payment information for developers"""
    if not settings.PAYMONGO_TEST_MODE:
        messages.error(request, "Test mode is not enabled.")
        return redirect('dashboard')
    
    paymongo = PayMongoService()
    
    context = {
        'test_cards': paymongo.get_test_card_numbers(),
        'test_gcash': paymongo.get_test_gcash_info(),
        'test_mode': True
    }
    
    return render(request, 'transactions/test_payment_info.html', context)

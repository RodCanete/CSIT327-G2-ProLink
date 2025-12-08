from django.urls import path
from . import views
from . import payment_views

app_name = 'transactions'

urlpatterns = [
    # PayMongo Payment flow
    path('<int:transaction_id>/pay/', payment_views.initiate_payment, name='initiate_payment'),
    path('<int:transaction_id>/payment-success/', payment_views.payment_success, name='paymongo_success'),
    path('<int:transaction_id>/payment-cancel/', payment_views.payment_cancel, name='paymongo_cancel'),
    path('webhook/paymongo/', payment_views.paymongo_webhook, name='paymongo_webhook'),
    path('test-payment-info/', payment_views.test_payment_info, name='test_payment_info'),
    
    # Legacy payment flow (keep for backward compatibility)
    path('pay/<int:request_id>/', views.create_payment, name='create_payment'),
    path('payment-success/<int:transaction_id>/', views.payment_success, name='payment_success'),
    
    # Work submission and approval
    path('submit-work/<int:request_id>/', views.submit_work, name='submit_work'),
    path('submission-success/<int:request_id>/', views.submission_success, name='submission_success'),
    path('approve-work/<int:request_id>/', views.approve_work, name='approve_work'),
    path('request-revision/<int:request_id>/', views.request_revision, name='request_revision'),
    
    # Dispute management
    path('open-dispute/<int:request_id>/', views.open_dispute, name='open_dispute'),
    path('dispute-submitted/<int:dispute_id>/', views.dispute_submitted, name='dispute_submitted'),
    path('dispute/<int:dispute_id>/', views.dispute_detail, name='dispute_detail'),
    path('submit-evidence/<int:dispute_id>/', views.submit_evidence, name='submit_evidence'),
    
    # Transaction history
    path('history/', views.transaction_history, name='history'),
    path('detail/<int:transaction_id>/', views.transaction_detail, name='detail'),
]

from django.db import models
from django.core.validators import MinValueValidator
from users.models import CustomUser
from requests.models import Request
from decimal import Decimal


class Transaction(models.Model):
    """
    Payment transactions with escrow support
    Tracks payments from client to professional with platform fee
    """
    STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),  # Client hasn't paid yet
        ('escrowed', 'Escrowed'),  # Money held, work in progress
        ('pending_approval', 'Pending Approval'),  # Work submitted, awaiting client approval
        ('completed', 'Completed'),  # Payment released to professional
        ('failed', 'Failed'),  # Payment failed
        ('refunded', 'Refunded'),  # Refunded to client
        ('disputed', 'Disputed'),  # Under dispute
    )
    
    request = models.OneToOneField(Request, on_delete=models.CASCADE, related_name='transaction')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments_made')
    professional = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments_received')
    
    # Payment amounts
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], 
                                 help_text="Total amount paid by client")
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                       help_text="ProLink's 10% commission")
    professional_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                              help_text="Amount professional receives after fee")
    
    # Transaction details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    payment_method = models.CharField(max_length=50, default='gcash', help_text="Payment method (GCash, etc)")
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True,
                                      help_text="External transaction ID (e.g., GCash reference)")
    gcash_number = models.CharField(max_length=15, blank=True, help_text="Client's GCash number")
    gcash_screenshot = models.TextField(blank=True, help_text="Path to payment proof screenshot")
    
    # Important dates
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True, help_text="When client paid")
    released_at = models.DateTimeField(null=True, blank=True, help_text="When payment released to professional")
    
    # Notes
    admin_notes = models.TextField(blank=True, help_text="Internal notes for dispute resolution")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"₱{self.amount} - {self.client.username} → {self.professional.username} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Calculate platform fee (10%) and professional payout (90%)
        if self.amount:
            self.platform_fee = (self.amount * Decimal('0.10')).quantize(Decimal('0.01'))
            self.professional_payout = (self.amount * Decimal('0.90')).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)


class Dispute(models.Model):
    """
    Dispute resolution system for transactions
    """
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved_client', 'Resolved - Favor Client'),
        ('resolved_professional', 'Resolved - Favor Professional'),
        ('resolved_partial', 'Resolved - Partial Refund'),
        ('closed', 'Closed'),
    )
    
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='dispute')
    opened_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='disputes_opened')
    
    # Dispute details
    reason = models.TextField(help_text="Why the dispute was opened")
    client_evidence = models.TextField(blank=True, help_text="Client's evidence/explanation")
    professional_evidence = models.TextField(blank=True, help_text="Professional's evidence/explanation")
    client_files = models.TextField(blank=True, help_text="JSON array of file paths")
    professional_files = models.TextField(blank=True, help_text="JSON array of file paths")
    
    # Resolution
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open')
    resolved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='disputes_resolved', help_text="Admin who resolved")
    resolution_notes = models.TextField(blank=True, help_text="Admin's decision and reasoning")
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                       help_text="Amount refunded to client (if any)")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dispute'
        verbose_name_plural = 'Disputes'
    
    def __str__(self):
        return f"Dispute #{self.id} - {self.transaction} - {self.get_status_display()}"


class WithdrawalRequest(models.Model):
    """
    Withdrawal requests from professionals
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('gcash', 'GCash'),
        ('bank_transfer', 'Bank Transfer'),
    )
    
    professional = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='gcash')
    gcash_number = models.CharField(max_length=15, blank=True, help_text="Professional's GCash number")
    bank_name = models.CharField(max_length=100, blank=True, help_text="Bank name for bank transfer")
    bank_account_number = models.CharField(max_length=50, blank=True, help_text="Bank account number")
    bank_account_name = models.CharField(max_length=100, blank=True, help_text="Account holder name")
    
    # Admin notes
    admin_notes = models.TextField(blank=True, help_text="Internal notes for processing")
    processed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='withdrawals_processed', help_text="Admin who processed")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Withdrawal Request'
        verbose_name_plural = 'Withdrawal Requests'
    
    def __str__(self):
        return f"Withdrawal ₱{self.amount} - {self.professional.username} - {self.get_status_display()}"
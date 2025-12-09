from django.contrib import admin
from .models import Transaction, Dispute, WithdrawalRequest


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'client', 'professional', 'amount', 'platform_fee', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('transaction_id', 'client__username', 'professional__username', 'gcash_number')
    readonly_fields = ('platform_fee', 'professional_payout', 'created_at', 'paid_at', 'released_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('request', 'client', 'professional', 'status')
        }),
        ('Payment Amounts', {
            'fields': ('amount', 'platform_fee', 'professional_payout')
        }),
        ('Payment Info', {
            'fields': ('payment_method', 'transaction_id', 'gcash_number', 'gcash_screenshot')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'paid_at', 'released_at')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction', 'opened_by', 'status', 'created_at', 'resolved_by')
    list_filter = ('status', 'created_at', 'resolved_at')
    search_fields = ('transaction__transaction_id', 'opened_by__username', 'reason')
    readonly_fields = ('created_at', 'resolved_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Dispute Info', {
            'fields': ('transaction', 'opened_by', 'status', 'reason')
        }),
        ('Evidence', {
            'fields': ('client_evidence', 'client_files', 'professional_evidence', 'professional_files')
        }),
        ('Resolution', {
            'fields': ('resolved_by', 'resolution_notes', 'refund_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'resolved_at')
        }),
    )


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('professional', 'amount', 'payment_method', 'status', 'created_at', 'processed_by')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('professional__username', 'professional__email', 'gcash_number', 'bank_account_number')
    readonly_fields = ('created_at', 'processed_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Withdrawal Info', {
            'fields': ('professional', 'amount', 'status')
        }),
        ('Payment Details - GCash', {
            'fields': ('payment_method', 'gcash_number'),
            'classes': ('collapse',)
        }),
        ('Payment Details - Bank', {
            'fields': ('bank_name', 'bank_account_number', 'bank_account_name'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('processed_by', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at')
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_completed']
    
    def mark_as_processing(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='processing', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} withdrawal(s) marked as processing.")
    mark_as_processing.short_description = "Mark selected as Processing"
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='completed', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} withdrawal(s) marked as completed.")
    mark_as_completed.short_description = "Mark selected as Completed"

from django.contrib import admin
from .models import Transaction, Dispute


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

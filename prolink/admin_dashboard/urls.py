from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.admin_users, name='users'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('requests/', views.admin_requests, name='requests'),
    path('transactions/', views.admin_transactions, name='transactions'),
    path('disputes/', views.admin_disputes, name='disputes'),
    path('disputes/<int:dispute_id>/', views.admin_dispute_detail, name='dispute_detail'),
    path('professionals/', views.admin_professionals, name='professionals'),
    path('professionals/<int:professional_id>/toggle-verification/', views.toggle_professional_verification, name='toggle_verification'),
    path('withdrawals/', views.withdrawal_requests, name='withdrawal_requests'),
    path('withdrawals/<int:withdrawal_id>/approve/', views.approve_withdrawal, name='approve_withdrawal'),
    path('withdrawals/<int:withdrawal_id>/reject/', views.reject_withdrawal, name='reject_withdrawal'),
]


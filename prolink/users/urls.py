from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("login/", views.login, name="login"),
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout, name="logout"),
    path('terms/', views.terms, name="terms"),
    path('privacy/', views.privacy, name="privacy"),
    
    # User Profile & Settings
    path('profile/', views.user_profile, name='profile'),
    path('settings/', views.user_settings, name='settings'),
    path('transactions/', views.transactions, name='transactions'),
    path('edit-profile-picture/', views.edit_profile_picture, name='edit_profile_picture'),
    path('check-profile-picture/', views.check_profile_picture, name='check_profile_picture'),  # Diagnostic
    
    
    # Professional URLs
    path('professionals/', views.find_professionals, name='find_professionals'),
    path('professionals/<int:pk>/', views.professional_detail, name='professional_detail'),
    path('professionals/<int:pk>/save/', views.save_professional, name='save_professional'),
    path('professionals/<int:pk>/unsave/', views.unsave_professional, name='unsave_professional'),
    path('saved/', views.saved_professionals_list, name='saved_professionals'),

    # API
    path('api/professionals/', views.professionals_api, name='professionals_api'),
]

from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("login/", views.login, name="login"),
    path("signup/", views.signup, name="signup"),
    path("registration-success/", views.registration_success, name="registration_success"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout, name="logout"),
    path('terms/', views.terms, name="terms"),
    path('privacy/', views.privacy, name="privacy"),
    path('dashboard/', views.dashboard_client, name='dashboard_client'),
    path('profile/', views.client_profile, name='client_profile'),
]
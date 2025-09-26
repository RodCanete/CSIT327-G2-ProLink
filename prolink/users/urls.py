from django.urls import path
from . import views

urlpatterns = [
    path("", views.login, name="users_login"),
]
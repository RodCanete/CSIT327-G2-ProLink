from django.urls import path
from . import views

urlpatterns = [
    path("", views.requests_list, name="requests_list"),
    path("<int:request_id>/message/", views.send_message, name="send_message"),
    path("<int:request_id>/cancel/", views.cancel_request, name="cancel_request"),
]

from django.urls import path
from . import views

urlpatterns = [
    path("", views.requests_list, name="requests_list"),
    path("create/", views.create_request, name="create_request"),
    path("<int:request_id>/", views.request_detail, name="request_detail"),
    path("<int:request_id>/message/", views.send_message, name="send_message"),
    path("<int:request_id>/cancel/", views.cancel_request, name="cancel_request"),
]

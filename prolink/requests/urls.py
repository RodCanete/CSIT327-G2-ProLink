from django.urls import path
from . import views

# Note: app_name not set to maintain backward compatibility with existing templates
# that reference URLs without namespace (e.g., 'request_detail' instead of 'requests:request_detail')

urlpatterns = [
    path("", views.requests_list, name="requests_list"),
    path("professional/", views.professional_requests_list, name="professional_requests_list"),
    path("create/", views.create_request, name="create_request"),
    path("test-upload/", views.test_upload_page, name="test_upload"),
    path("<int:request_id>/", views.request_detail, name="request_detail"),
    path("professional/<int:request_id>/", views.professional_request_detail, name="professional_request_detail"),
    path("<int:request_id>/edit/", views.edit_request, name="edit_request"),
    path("<int:request_id>/delete/", views.delete_request, name="delete_request"),
    path("<int:request_id>/message/", views.send_message, name="send_message"),
    path("<int:request_id>/cancel/", views.cancel_request, name="cancel_request"),
    path("<int:request_id>/pay/", views.pay_request, name="pay_request"),
    # Professional acceptance
    path("<int:request_id>/accept/", views.accept_request, name="accept_request"),
]

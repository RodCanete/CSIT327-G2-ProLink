from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('api/count/', views.get_notification_count, name='count'),
    path('api/list/', views.get_notifications, name='list'),
    path('api/<int:notification_id>/read/', views.mark_notification_read, name='mark_read'),
    path('api/mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
]


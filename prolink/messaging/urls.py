from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('api/unread-count/', views.get_unread_count, name='unread_count'),
    path('api/<int:conversation_id>/new-messages/', views.get_new_messages, name='new_messages'),
]

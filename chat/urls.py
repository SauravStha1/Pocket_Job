from django.urls import path
from . import views

urlpatterns = [
    path('start/<int:application_id>/<int:job_id>/', views.start_chat, name='start_chat'),
    path('room/<int:chatroom_id>/', views.chat_room, name='chat_room'),
    path('my-chats/', views.my_chats, name='my_chats'),  # applicant inbox
    path('inbox/', views.inbox, name='inbox'),
]
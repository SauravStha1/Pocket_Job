from django.urls import path
from .views import profile_view, register, login_view, verify_otp, notifications_view, notification_api, mark_notification_read
from accounts import views

urlpatterns = [
    path("register/", register, name="register"),
    path("verify-otp/", verify_otp, name="verify_otp"),
    path("login/", login_view, name="login"),
    path("profile/", profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path('notifications/', notifications_view, name='notifications'),
    path('api/notifications/', notification_api, name='notification_api'),
    path('api/notification/read/<int:id>/', mark_notification_read, name='mark_notification_read'),
]
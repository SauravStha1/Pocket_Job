from django.urls import path
from .views import register, login_view, verify_otp

urlpatterns = [
    path("register/", register, name="register"),
    path("verify-otp/", verify_otp, name="verify_otp"),
    path("login/", login_view, name="login"),
]
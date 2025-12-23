from django.urls import path
from . import views

urlpatterns = [
    path('', views.role_select, name='role_select'),
    path('login/applicant/', views.applicant_login, name='applicant_login'),
    path('login/recruiter/', views.recruiter_login, name='recruiter_login'),
    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
]

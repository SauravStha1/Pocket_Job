from django.urls import path
from . import views
from .views import admin_revenue, apply_job, recruiter_dashboard, job_applicants, accept_application, reject_application

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('create/', views.job_create, name='job_create'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    path ('pay/<int:id>/', views.pay_job, name='pay_job'),

    path('test_esewa/', views.test_esewa, name='test_esewa'),

    path('job/<int:pk>/apply/', apply_job, name='apply_job'),
    path('recruiter/dashboard/', recruiter_dashboard, name='recruiter_dashboard'),
    path('recruiter/job/<int:pk>/applicants/', job_applicants, name='job_applicants'),
    path('application/<int:id>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:id>/reject/', views.reject_application, name='reject_application'),
    path('my-applications/', views.applied_jobs, name='applied_jobs'),

    path('save/<int:pk>/', views.toggle_save_job, name='toggle_save_job'),
    path('saved/', views.saved_jobs, name='saved_jobs'),

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('admin/applicants/', views.view_applicants, name='view_applicants'),
    path('admin/recruiters/', views.view_recruiters, name='view_recruiters'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),

    path('recruiter/jobs/', views.recruiter_jobs, name='recruiter_jobs'),
    path('recruiter/applicants/', views.applied_applicants, name='applied_applicants'),
    path('admin/revenue/', admin_revenue, name='admin_revenue'),

    path('khalti/initiate/<int:payment_id>/', views.khalti_initiate, name='khalti_initiate'),
    path('khalti/callback/', views.khalti_callback, name='khalti_callback'),
    path('khalti/<int:payment_id>/', views.khalti_payment, name='khalti_payment'),
    path('khalti/verify/', views.khalti_verify, name='khalti_verify'),

    path('admin/profile/<int:user_id>/', views.admin_view_profile, name='admin_view_profile'),
    path('ban-user/<int:user_id>/', views.ban_user, name='ban_user'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('create/', views.job_create, name='job_create'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    path ('pay/<int:id>/', views.pay_job, name='pay_job'),

    path('test_esewa/', views.test_esewa, name='test_esewa'),
]
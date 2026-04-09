from django.urls import path
from . import views

urlpatterns = [
    path('report/job/<int:job_id>/', views.report_job, name='report_job'),
    path('report/user/<int:user_id>/', views.report_user, name='report_user'),

    path('reports/', views.admin_reports, name='admin_reports'),
    path('delete-job/<int:job_id>/', views.delete_reported_job, name='delete_reported_job'),
    path('ban-user/<int:user_id>/', views.ban_user, name='ban_user'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('resolve/<int:report_id>/', views.resolve_report, name='resolve_report'),

]
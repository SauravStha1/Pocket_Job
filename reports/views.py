from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from Job_Post.models import Job
from .models import Report
from accounts.models import Notification


# 🚨 REPORT JOB
@login_required
def report_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":
        reason = request.POST.get('reason', '')

        Report.objects.create(
            reporter=request.user,
            report_type='job',
            job=job,
            reason=reason,
            status='PENDING'
        )

        # 🔔 Notify admins
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"{request.user.username} reported job '{job.title}'",
                notification_type='report',
                link="/admin/reports/"
            )

    return redirect('job_detail', pk=job.id)


# 🚨 REPORT USER
@login_required
def report_user(request, user_id):
    reported_user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        reason = request.POST.get('reason', '')

        Report.objects.create(
            reporter=request.user,
            report_type='user',
            reported_user=reported_user,
            reason=reason,
            status='PENDING'
        )

        # 🔔 Notify admins
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"{request.user.username} reported user '{reported_user.username}'",
                notification_type='report',
                link="/admin/reports/"
            )

    return redirect('home')


# 🧑‍💼 ADMIN VIEW REPORTS
@staff_member_required
def admin_reports(request):
    filter_type = request.GET.get('filter', 'all')

    reports = Report.objects.all().order_by('-id')

    if filter_type == 'pending':
        reports = reports.filter(status='PENDING')
    elif filter_type == 'job':
        reports = reports.filter(report_type='job')
    elif filter_type == 'user':
        reports = reports.filter(report_type='user')

    context = {
        'reports': reports,
        'current_filter': filter_type
    }

    return render(request, 'reports/admin_reports.html', context)


# ❌ DELETE JOB
@staff_member_required
def delete_reported_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.delete()
    return redirect('admin_reports')


# 🚫 BAN USER
@staff_member_required
def ban_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    return redirect('admin_reports')

@staff_member_required
def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    return render(request, 'reports/report_detail.html', {
        'report': report
    })

@staff_member_required
def resolve_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    report.status = 'RESOLVED'
    report.save()

    messages.success(request, "Report marked as resolved.")

    return redirect('admin_reports')
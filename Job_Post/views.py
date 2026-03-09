from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from .models import Job
from .forms import JobForm
from accounts.models import Profile


# ============================
# PUBLIC JOB LIST (Applicants)
# ============================
def job_list(request):
    jobs = Job.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'Job_Post/job_list.html', {'jobs': jobs})


# ============================
# RECRUITER DASHBOARD
# ============================
@login_required
def recruiter_dashboard(request):

    if request.user.profile.role != "RECRUITER":
        messages.error(request, "Access denied.")
        return redirect("home")

    jobs = Job.objects.filter(recruiter=request.user, is_active=True)
    return render(request, 'Job_Post/recruiter_dashboard.html', {'jobs': jobs})


# ============================
# CREATE JOB (Recruiter Only)
# ============================
@login_required
@transaction.atomic
def job_create(request):

    if request.user.profile.role != "RECRUITER":
        messages.error(request, "Only recruiters can post jobs.")
        return redirect("home")

    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)  # UPDATED
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.save()
            messages.success(request, "Job posted successfully.")
            return redirect("recruiter_dashboard")
    else:
        form = JobForm()

    return render(request, 'Job_Post/job_form.html', {'form': form})


# ============================
# JOB DETAIL (Public)
# ============================
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    return render(request, 'Job_Post/job_detail.html', {'job': job})


# ============================
# EDIT JOB (Owner Only)
# ============================
@login_required
@transaction.atomic
def job_edit(request, pk):

    job = get_object_or_404(
        Job,
        pk=pk,
        recruiter=request.user,
        is_active=True
    )

    if request.user.profile.role != "RECRUITER":
        messages.error(request, "Access denied.")
        return redirect("home")

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES, instance=job)  # UPDATED
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect("recruiter_dashboard")
    else:
        form = JobForm(instance=job)

    return render(request, "Job_Post/job_form.html", {"form": form})


# ============================
# DELETE JOB (Soft Delete)
# ============================
@login_required
@transaction.atomic
def job_delete(request, pk):

    job = get_object_or_404(
        Job,
        pk=pk,
        recruiter=request.user,
        is_active=True
    )

    if request.user.profile.role != "RECRUITER":
        messages.error(request, "Access denied.")
        return redirect("home")

    job.is_active = False
    job.save()

    messages.success(request, "Job deleted successfully.")
    return redirect("recruiter_dashboard")
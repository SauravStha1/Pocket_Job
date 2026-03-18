from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Job, JobApplication  # Added JobApplication
from .forms import JobForm
from .payment_models import Payment
from accounts.models import Profile

from django.conf import settings
import hmac
import hashlib
import base64
import uuid
import json

# ============================
# PUBLIC JOB LIST (Applicants)
# ============================

def generate_signature(total_amount, transaction_uuid, product_code='EPAYTEST'):
    """Generate HMAC SHA256 signature for eSewa"""
    secret_key = settings.ESEWA_SECRET_KEY
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"

    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()

    signature_base64 = base64.b64encode(signature).decode('utf-8')
    return signature_base64


def job_list(request):
    if request.user.is_authenticated and request.user.profile.role == "RECRUITER":
        jobs = Job.objects.filter(
            recruiter=request.user,
            is_active=True
        ).order_by('-created_at')
    else:
        jobs = Job.objects.filter(
            is_active=True,
            deadline__gte=timezone.now()
        ).order_by('-created_at')
    return render(request, 'Job_Post/job_list.html', {'jobs': jobs})


# ============================
# JOB DETAIL (Public)
# ============================

def job_detail(request, pk):

    job = get_object_or_404(
        Job,
        pk=pk,
        is_active=True
    )

    has_applied = False

    if request.user.is_authenticated and request.user.profile.role == "APPLICANT":
        has_applied = JobApplication.objects.filter(
            job=job,
            applicant=request.user.profile
        ).exists()

    return render(request, 'Job_Post/job_detail.html', {
        'job': job,
        'has_applied': has_applied
    })


# ============================
# APPLY JOB (One-Click)
# ============================

@login_required
def apply_job(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)

    if request.user.profile.role != "APPLICANT":
        messages.error(request, "Only applicants can apply for jobs.")
        return redirect('job_list')

    profile = request.user.profile

    # Prevent duplicate application
    if JobApplication.objects.filter(job=job, applicant=profile).exists():
        messages.warning(request, "You have already applied for this job.")
    else:
        JobApplication.objects.create(job=job, applicant=profile)
        messages.success(request, "You have successfully applied for this job.")

    return redirect('job_detail', pk=job.pk)


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
# LIST APPLICANTS (Recruiter)
# ============================

@login_required
def job_applicants(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    applications = job.applications.all()  # thanks to related_name
    return render(request, 'Job_Post/job_applicants.html', {'job': job, 'applications': applications})


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
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.deadline = timezone.now() + timedelta(days=30)
            job.is_active = False  # job inactive until payment
            job.save()

            payment = Payment.objects.create(
                recruiter=request.user,
                job=job,
                amount=1000
            )

            messages.success(request, "Job created. Please complete payment to publish the job.")
            return redirect('pay_job', id=payment.id)
    else:
        form = JobForm()

    return render(request, 'Job_Post/job_form.html', {'form': form})


# ============================
# PAY JOB / PAYMENT SUCCESS / FAILURE
# ============================
# ============================
# PAY JOB (Redirect to eSewa)
# ============================

def test_esewa(request):

    transaction_uuid = str(uuid.uuid4())
    amount = 1000

    esewa_context = {
        'amount': amount,
        'transaction_uuid': transaction_uuid,
        'product_code': settings.ESEWA_MERCHANT_CODE,
        'signature': generate_signature(amount, transaction_uuid),
        'esewa_url': settings.ESEWA_URL,
        'success_url': request.build_absolute_uri('/jobs/payment/success/'),
        'failure_url': request.build_absolute_uri('/jobs/payment/failure/'),
    }

    return render(request, "Job_Post/esewa_form.html", esewa_context)


@login_required
def pay_job(request, id):

    payment = get_object_or_404(Payment, id=id)

    esewa_context = {
        'amount': payment.amount,
        'transaction_uuid': str(payment.transaction_uuid),
        'product_code': settings.ESEWA_MERCHANT_CODE,
        'signature': generate_signature(payment.amount, str(payment.transaction_uuid)),
        'esewa_url': settings.ESEWA_URL,
        'success_url': request.build_absolute_uri('/jobs/payment/success/'),
        'failure_url': request.build_absolute_uri('/jobs/payment/failure/'),
        "payment": payment
    }

    return render(request, "Job_Post/esewa_form.html", esewa_context)


# ============================
# PAYMENT SUCCESS (FIXED)
# ============================

@login_required
def payment_success(request):

    data = request.GET.get("data")

    if not data:
        return redirect("job_list")

    try:
        decoded_data = base64.b64decode(data).decode("utf-8")
        payment_data = json.loads(decoded_data)

        transaction_uuid = payment_data.get("transaction_uuid")
        status = payment_data.get("status")

        payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid)

        if status == "COMPLETE":
            payment.status = "COMPLETED"
            payment.save()

            job = payment.job
            job.is_active = True
            job.save()

            return render(request, "payments/success.html")

        else:
            payment.status = "FAILED"
            payment.save()

            return render(request, "payments/failure.html")

    except Exception:
        return render(request, "payments/failure.html")


# ============================
# PAYMENT FAILURE (FIXED)
# ============================

@login_required
def payment_failure(request):

    data = request.GET.get("data")

    if data:
        try:
            decoded_data = base64.b64decode(data).decode("utf-8")
            payment_data = json.loads(decoded_data)

            transaction_uuid = payment_data.get("transaction_uuid")

            payment = Payment.objects.filter(transaction_uuid=transaction_uuid).first()

            if payment:
                payment.status = "FAILED"
                payment.save()
        except:
            pass

    return render(request, "payments/failure.html")

# ...
# ============================


# ============================
# EDIT JOB
# ============================

@login_required
@transaction.atomic
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect("recruiter_dashboard")
    else:
        form = JobForm(instance=job)

    return render(request, "Job_Post/job_form.html", {"form": form})


# ============================
# DELETE JOB
# ============================

@login_required
@transaction.atomic
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    job.is_active = False
    job.save()
    messages.success(request, "Job deleted successfully.")
    return redirect("recruiter_dashboard")

# ============================
# ALL APPLIED APPLICANTS (Recruiter)
# ============================

@login_required
def applied_applicants(request):
    if request.user.profile.role != "RECRUITER":
        messages.error(request, "Access denied.")
        return redirect("home")

    applications = JobApplication.objects.filter(
        job__recruiter=request.user
    ).select_related('applicant', 'job').order_by('-applied_at')

    return render(request, 'Job_Post/applied_applicants.html', {
        'applications': applications
    })


# ============================
# ACCEPT APPLICATION
# ============================

@login_required
def accept_application(request, id):
    application = get_object_or_404(JobApplication, id=id, job__recruiter=request.user)
    application.status = "ACCEPTED"
    application.save()

    messages.success(request, "Applicant accepted.")
    return redirect('applied_applicants')


# ============================
# REJECT APPLICATION
# ============================

@login_required
def reject_application(request, id):
    application = get_object_or_404(JobApplication, id=id, job__recruiter=request.user)
    application.status = "REJECTED"
    application.save()

    messages.warning(request, "Applicant rejected.")
    return redirect('applied_applicants')

@login_required
def applied_jobs(request):
    if request.user.profile.role != "APPLICANT":
        messages.error(request, "Access denied.")
        return redirect("home")

    applications = JobApplication.objects.filter(
        applicant=request.user.profile
    ).select_related('job').order_by('-applied_at')

    return render(request, 'Job_Post/applied_jobs.html', {
        'applications': applications
    })
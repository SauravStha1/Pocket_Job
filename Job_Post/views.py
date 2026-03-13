from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Job
from .forms import JobForm
from .payment_models import Payment
from accounts.models import Profile

from django.conf import settings
import hmac
import hashlib
import base64
import uuid
# ============================
# PUBLIC JOB LIST (Applicants)
# ============================

 
def generate_signature(total_amount, transaction_uuid, product_code='EPAYTEST'):
    """Generate HMAC SHA256 signature for eSewa"""
    secret_key = settings.ESEWA_SECRET_KEY
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"

    # Create HMAC SHA256 signature
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()

    # Encode to base64
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
# RECRUITER DASHBOARD
# ============================
@login_required
def recruiter_dashboard(request):

    if request.user.profile.role != "RECRUITER":
        messages.error(request, "Access denied.")
        return redirect("home")

    jobs = Job.objects.filter(recruiter=request.user)

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

        form = JobForm(request.POST, request.FILES)

        if form.is_valid():

            job = form.save(commit=False)
            job.recruiter = request.user
            job.deadline = timezone.now() + timedelta(days=30)

            # IMPORTANT: job inactive until payment
            job.is_active = False
            job.save()

            # Create payment record
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
        'success_url': request.build_absolute_uri('/payment/success/'),
        'failure_url': request.build_absolute_uri('/payment/failure/'),
    }

    return render(request, "Job_Post/esewa_form.html", esewa_context)



@login_required
def pay_job(request, id):

    payment = get_object_or_404(Payment, id=id)
    transaction_uuid = str(payment.transaction_uuid)
    signature = generate_signature(payment.amount, transaction_uuid)
  

    esewa_context = {
        'amount': payment.amount,
        'transaction_uuid': str(payment.transaction_uuid),
        'product_code': settings.ESEWA_MERCHANT_CODE,
        'signature': generate_signature(payment.amount, str(payment.transaction_uuid)),
        'esewa_url': settings.ESEWA_URL,
        'success_url': request.build_absolute_uri('/payment/success/'),
        'failure_url': request.build_absolute_uri('/payment/failure/'),
        "payment": payment
    }
    return render(request, "Job_Post/esewa_form.html", esewa_context)


# ============================
# PAYMENT SUCCESS
# ============================
@login_required
def payment_success(request):

    transaction_uuid = request.GET.get("transaction_uuid")

    payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid)

    payment.status = "COMPLETED"
    payment.save()

    job = payment.job
    job.is_active = True
    job.save()

    return render(request, "payments/success.html")


# ============================
# PAYMENT FAILURE
# ============================
@login_required
def payment_failure(request):

    transaction_uuid = request.GET.get("transaction_uuid")

    payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid)

    payment.status = "FAILED"
    payment.save()

    return render(request, "payments/failure.html")


# ============================
# JOB DETAIL (Public)
# ============================
def job_detail(request, pk):

    job = get_object_or_404(
        Job,
        pk=pk,
        is_active=True
    )

    return render(request, 'Job_Post/job_detail.html', {'job': job})


# ============================
# EDIT JOB
# ============================
@login_required
@transaction.atomic
def job_edit(request, pk):

    job = get_object_or_404(
        Job,
        pk=pk,
        recruiter=request.user
    )

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

    job = get_object_or_404(
        Job,
        pk=pk,
        recruiter=request.user
    )

    job.is_active = False
    job.save()

    messages.success(request, "Job deleted successfully.")

    return redirect("recruiter_dashboard")
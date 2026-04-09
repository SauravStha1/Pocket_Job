from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import recruiter_required, applicant_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncMonth

from .models import Job, JobApplication
from .models import SavedJob  
from .forms import JobForm
from .payment_models import Payment
from accounts.models import Profile
from accounts.models import Notification
from django.db.models import Sum

from django.conf import settings
import hmac
import hashlib
import base64
import uuid
import json
import requests


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

    is_saved = False

    if request.user.is_authenticated:
        from .models import SavedJob
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    return render(request, 'Job_Post/job_detail.html', {
        'job': job,
        'has_applied': has_applied,
        'is_saved': is_saved
    })

# ============================
# APPLY JOB (One-Click)
# ============================
@login_required
@applicant_required
def apply_job(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    profile = request.user.profile

    if JobApplication.objects.filter(job=job, applicant=profile).exists():
        messages.warning(request, "You have already applied for this job.")
    else:
        JobApplication.objects.create(job=job, applicant=profile)

        # 🔔 Notify recruiter
        create_notification(
            job.recruiter,
            f"{request.user.username} applied for your job '{job.title}'",
            "application",
            link=f"/jobs/{job.id}/"
        )

        messages.success(request, "You have successfully applied for this job.")

    return redirect('job_detail', pk=job.pk)

# ============================
# RECRUITER DASHBOARD
# ============================

@login_required
@recruiter_required
def recruiter_dashboard(request):
    jobs = Job.objects.filter(
        recruiter=request.user,
        is_active=True
    )

    # ✅ TOTAL APPLICANTS COUNT
    total_applicants = JobApplication.objects.filter(
        job__recruiter=request.user
    ).count()

    # ✅ OPTIONAL (extra stats - good for future charts)
    total_jobs = jobs.count()

    return render(request, 'Job_Post/recruiter_dashboard.html', {
        'jobs': jobs,
        'total_applicants': total_applicants,
        'total_jobs': total_jobs
    })

# ============================
# LIST APPLICANTS (Recruiter)
# ============================

@login_required
@recruiter_required
def job_applicants(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    applications = job.applications.all()  # thanks to related_name
    return render(request, 'Job_Post/job_applicants.html', {'job': job, 'applications': applications})


# ============================
# CREATE JOB (Recruiter Only)
# ============================

@login_required
@recruiter_required
@transaction.atomic
def job_create(request):
    if request.method == "POST":
        form = JobForm(request.POST, request.FILES)

        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.is_active = False  # wait until payment
            job.save()

            # ✅ GET PAYMENT METHOD FROM BUTTON
            payment_method = request.POST.get('payment_method')

            # ✅ CREATE PAYMENT OBJECT
            payment = Payment.objects.create(
                recruiter=request.user,
                job=job,
                amount=1000,
                payment_method=payment_method
            )

            # ✅ REDIRECT BASED ON PAYMENT METHOD
            if payment_method == "esewa":
                return redirect('pay_job', payment.id)

            elif payment_method == "khalti":
                return redirect('khalti_payment', payment.id)

    else:
        form = JobForm()

    return render(request, "Job_Post/job_form.html", {"form": form})

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

    if payment.payment_method == 'esewa':
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

    elif payment.payment_method == 'khalti':
        return redirect('khalti_initiate', payment_id=payment.id)

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
@recruiter_required
@transaction.atomic
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect("recruiter_jobs")
    else:
        form = JobForm(instance=job)

    return render(request, "Job_Post/job_form.html", {"form": form})


# ============================
# DELETE JOB
# ============================

@login_required

@transaction.atomic
@staff_member_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.is_active = False
    job.save()

    messages.success(request, "Job deleted by admin.")
    return redirect('job_list')

# ============================
# ALL APPLIED APPLICANTS (Recruiter)
# ============================

@login_required
@recruiter_required
def applied_applicants(request):

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
@recruiter_required
def accept_application(request, id):
    application = get_object_or_404(JobApplication, id=id, job__recruiter=request.user)
    application.status = "HIRED"
    application.save()

    # 🔔 Notify applicant
    create_notification(
        application.applicant.user,
        f"You got hired for '{application.job.title}' 🎉",
        "hired",
        link=f"/jobs/{application.job.id}/"
    )
    messages.success(request, "Applicant accepted.")
    return redirect('applied_applicants')

# ============================
# REJECT APPLICATION
# ============================

@login_required
@recruiter_required
def reject_application(request, id):
    application = get_object_or_404(JobApplication, id=id, job__recruiter=request.user)
    application.status = "REJECTED"
    application.save()

    # 🔔 Notify applicant
    create_notification(
        application.applicant.user,
        f"Your application for '{application.job.title}' was rejected",
        "rejected",
        link=f"/jobs/{application.job.id}/"
    )

    messages.warning(request, "Applicant rejected.")
    return redirect('applied_applicants')

@login_required
@applicant_required
def applied_jobs(request):
    applications = JobApplication.objects.filter(
        applicant=request.user.profile
    ).select_related('job').order_by('-applied_at')

    context = {
        'applications': applications,
        'total_applied': applications.count(),
        'hired_count': applications.filter(status='HIRED').count(),
        'pending_count': applications.filter(status='PENDING').count(),
        'rejected_count': applications.filter(status='REJECTED').count(),
    }

    return render(request, 'Job_Post/applied_jobs.html', context)


def create_notification(user, message, notification_type, link=None):
    Notification.objects.create(
        user=user,
        message=message,
        notification_type=notification_type,
        link=link
    )

@login_required
@applicant_required
def toggle_save_job(request, pk):
    job = get_object_or_404(Job, pk=pk) 
    saved_job = SavedJob.objects.filter(user=request.user, job=job)

    if saved_job.exists():
        saved_job.delete()
        messages.info(request, "Job removed from saved.")
    else:
        SavedJob.objects.create(user=request.user, job=job)
        messages.success(request, "Job saved successfully.")

    return redirect('job_detail', pk=pk)

@login_required
@applicant_required
def saved_jobs(request):

    saved_jobs = SavedJob.objects.filter(user=request.user).select_related('job').order_by('-saved_at')

    return render(request, 'Job_Post/saved_jobs.html', {
        'saved_jobs': saved_jobs
    })

def about(request):
    return render(request, "about.html")

# ============================
# ADMIN DASHBOARD
# ============================

@staff_member_required
def admin_dashboard(request):
    # ── User Stats ──
    total_users = User.objects.count()
    total_applicants = Profile.objects.filter(role='APPLICANT').count()
    total_recruiters = Profile.objects.filter(role='RECRUITER').count()

    # ── Job Stats ──
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(is_active=True).count()

    # ── Applications (if exists) ──
    total_applications = JobApplication.objects.count()

    # ── Revenue (if exists) ──
    total_revenue = 0
    if Payment:
        total_revenue = Payment.objects.filter(status='COMPLETED').aggregate(
            total=Sum('amount')
        )['total'] or 0

    # ── Latest Jobs & Applications ──
    latest_jobs = Job.objects.order_by('-created_at')[:10]
    latest_applications = JobApplication.objects.order_by('-applied_at')[:10]

    context = {
        'total_users': total_users,
        'total_applicants': total_applicants,
        'total_recruiters': total_recruiters,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'total_revenue': total_revenue,
        'latest_jobs': latest_jobs,
        'latest_applications': latest_applications,
    }

    return render(request, 'Job_Post/admin_dashboard.html', context)

@staff_member_required
def view_applicants(request):
    applicants = Profile.objects.filter(role='APPLICANT')
    return render(request, 'Job_Post/view_applicants.html', {
        'applicants': applicants
    })


@staff_member_required
def view_recruiters(request):
    recruiters = Profile.objects.filter(role='RECRUITER')
    return render(request, 'Job_Post/view_recruiters.html', {
        'recruiters': recruiters
    })

@staff_member_required
def admin_view_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Profile, user=user)

    jobs = None
    if profile.role == "RECRUITER":
        jobs = Job.objects.filter(recruiter=user)

    return render(request, 'Job_Post/admin_view_profile.html', {
        'profile_user': user,
        'profile': profile,
        'jobs': jobs
    })

@staff_member_required
def ban_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()

    messages.warning(request, f"{user.username} has been banned.")

    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

def admin_reports(request):
    return render(request, 'Job_Post/admin_reports.html')

# ============================
# RECRUITER JOB LIST (Posted Jobs Page)
# ============================

@login_required
@recruiter_required
def recruiter_jobs(request):
    jobs = Job.objects.filter(
        recruiter=request.user,
        is_active=True
    ).order_by('-created_at')
    total_applicants = JobApplication.objects.filter(job__recruiter=request.user).count()


    return render(request, 'Job_Post/job_list.html', {
        'jobs': jobs,
        'total_applicants': total_applicants,
    })


@login_required
def khalti_initiate(request, payment_id):

    payment = get_object_or_404(Payment, id=payment_id)

    payload = {
        "return_url": request.build_absolute_uri('/jobs/khalti/callback/'),
        "website_url": request.build_absolute_uri('/'),
        "amount": payment.amount * 100,
        "purchase_order_id": str(payment.transaction_uuid),
        "purchase_order_name": f"Job Payment {payment.job.id}",
    }

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://dev.khalti.com/api/v2/epayment/initiate/",
        json=payload,
        headers=headers
    )

    data = response.json()

    if response.status_code == 200:
        return redirect(data["payment_url"])
    else:
        payment.status = "FAILED"
        payment.save()
        messages.error(request, "Khalti initiation failed")
        return redirect('job_list')

@login_required
def khalti_callback(request):

    pidx = request.GET.get('pidx')
    purchase_order_id = request.GET.get('purchase_order_id')

    payment = get_object_or_404(Payment, transaction_uuid=purchase_order_id)

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://dev.khalti.com/api/v2/epayment/lookup/",
        json={"pidx": pidx},
        headers=headers
    )

    data = response.json()

    if data.get("status") == "Completed":
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
    
def khalti_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    url = "https://dev.khalti.com/api/v2/epayment/initiate/"

    payload = {
        "return_url": request.build_absolute_uri(f'/jobs/khalti/verify/?payment_id={payment.id}'),
        "website_url": "http://127.0.0.1:8000/",
        "amount": payment.amount * 100,
        "purchase_order_id": str(payment.transaction_uuid),
        "purchase_order_name": payment.job.title,
    }

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)  # IMPORTANT

    if response.status_code == 200:
        data = response.json()
        return redirect(data["payment_url"])
    else:
        return HttpResponse(response.text)



@csrf_exempt
def khalti_verify(request):
    payment_id = request.GET.get("payment_id")
    pidx = request.GET.get("pidx")

    payment = get_object_or_404(Payment, id=payment_id)

    url = "https://dev.khalti.com/api/v2/epayment/lookup/"

    payload = json.dumps({
        "pidx": pidx
    })

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, data=payload)
    data = response.json()

    if data.get("status") == "Completed":
        payment.status = "COMPLETED"
        payment.job.is_active = True

        payment.job.save()
        payment.save()

        return render(request, "payments/success.html")

    else:
        payment.status = "FAILED"
        payment.save()

        return HttpResponse("❌ Payment Failed")


@staff_member_required
def admin_revenue(request):

    filter_type = request.GET.get('filter', 'all')

    payments = Payment.objects.filter(status='COMPLETED')

    # ✅ APPLY DATE FILTER
    if filter_type == 'today':
        payments = payments.filter(created_at__date=timezone.now().date())

    elif filter_type == 'week':
        payments = payments.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        )

    elif filter_type == 'month':
        payments = payments.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )

    # ✅ TOTALS
    total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0

    esewa_total = payments.filter(payment_method='esewa').aggregate(total=Sum('amount'))['total'] or 0
    khalti_total = payments.filter(payment_method='khalti').aggregate(total=Sum('amount'))['total'] or 0

    # ✅ CHART DATA
    chart_qs = payments.annotate(date=TruncDate('created_at')) \
                       .values('date') \
                       .annotate(total=Sum('amount')) \
                       .order_by('date')

    chart_labels = [str(item['date']) for item in chart_qs]
    chart_data = [item['total'] for item in chart_qs]
    # 📊 MONTHLY CHART DATA (Jan, Feb, Mar...)
    monthly_qs = payments.annotate(month=TruncMonth('created_at')) \
                        .values('month') \
                        .annotate(total=Sum('amount')) \
                        .order_by('month')

    monthly_labels = [
        item['month'].strftime('%b') for item in monthly_qs
    ]

    monthly_data = [item['total'] for item in monthly_qs]

    context = {
        'payments': payments.order_by('-created_at')[:20],
        'total_revenue': total_revenue,
        'esewa_total': esewa_total,
        'khalti_total': khalti_total,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'current_filter': filter_type,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
    }

    return render(request, 'Job_Post/revenue.html', context)
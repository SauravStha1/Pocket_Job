from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.conf import settings
from django.core.files.base import ContentFile

from .models import Profile
import random
from .models import Notification
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
from .models import EmailOTP

# =========================
# LOGIN VIEW
# =========================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")  # no need role check here
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


# =========================
# STEP 1: REGISTER VIEW
# =========================
def register(request):
    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        profile_pic = request.FILES.get("profile_pic")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        if not username or not email or not password or not role:
            messages.error(request, "All fields are required.")
            return redirect("register")

        otp = random.randint(100000, 999999)

        # Save registration info in session
        request.session["register_data"] = {
            "username": username,
            "email": email,
            "password": password,
            "role": role
        }

        # Save image temporarily in session
        if profile_pic:
            request.session["profile_pic_name"] = profile_pic.name
            request.session["profile_pic_file"] = profile_pic.read().decode("latin1")

        request.session["register_otp"] = str(otp)

        # Send OTP email
        send_mail(
            subject="Pocket Job - OTP Verification",
            message=f"Your OTP code is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "OTP has been sent to your email.")
        return redirect("verify_otp")

    return render(request, "accounts/register.html")


# =========================
# STEP 2: VERIFY OTP VIEW
# =========================
def verify_otp(request):
    if request.method == "POST":

        otp_entered = request.POST.get("otp")
        session_otp = request.session.get("register_otp")
        data = request.session.get("register_data")

        if not session_otp or not data:
            messages.error(request, "Session expired. Please register again.")
            return redirect("register")

        if otp_entered != session_otp:
            messages.error(request, "Invalid OTP.")
            return redirect("verify_otp")

        # ❌ REMOVE duplicate logic
        # ✅ ALWAYS create user once
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"]
        )

        # ✅ USE SIGNAL PROFILE (important)
        profile = user.profile
        profile.role = data["role"]
        profile.save()

        # Restore image
        profile_pic_name = request.session.get("profile_pic_name")
        profile_pic_file = request.session.get("profile_pic_file")

        if profile_pic_name and profile_pic_file:
            image_file = ContentFile(
                profile_pic_file.encode("latin1"),
                name=profile_pic_name
            )
            profile.profile_pic.save(profile_pic_name, image_file, save=True)

        # ✅ CLEAR FULL SESSION (important fix)
        request.session.flush()

        login(request, user)
        return redirect("home")

    return render(request, "accounts/verify_otp.html")

# =========================
# PROFILE PAGE
# =========================
def profile_view(request):

    if not request.user.is_authenticated:
        return redirect("login")

    profile = request.user.profile

    return render(request, "accounts/profile.html", {"profile": profile})

# =========================
# EDIT PROFILE
# =========================

def edit_profile(request):

    if not request.user.is_authenticated:
        return redirect("login")

    profile = request.user.profile

    if request.method == "POST":

        # Applicant fields
        profile.full_name = request.POST.get("full_name")
        profile.age = request.POST.get("age")
        profile.skills = request.POST.get("skills")
        profile.location = request.POST.get("location")
        profile.contact_email = request.POST.get("contact_email")
        profile.description = request.POST.get("description")

        if request.FILES.get("cv"):
            profile.cv = request.FILES.get("cv")

        # Recruiter fields
        profile.company_name = request.POST.get("company_name")
        profile.owner_name = request.POST.get("owner_name")
        profile.company_location = request.POST.get("company_location")
        profile.company_type = request.POST.get("company_type")
        profile.phone = request.POST.get("phone")
        profile.company_email = request.POST.get("company_email")
        profile.founded_date = request.POST.get("founded_date")

        if request.FILES.get("profile_pic"):
            profile.profile_pic = request.FILES.get("profile_pic")

        profile.save()

        messages.success(request, "Profile updated successfully!")

        return redirect("profile")

    return render(request, "accounts/edit_profile.html", {"profile": profile})

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # mark all as read
    notifications.update(is_read=True)

    return render(request, 'accounts/notifications.html', {
        'notifications': notifications
    })

@login_required
def notification_api(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]

    data = []

    for n in notifications:
        data.append({
            "id": n.id,
            "message": n.message,
            "link": n.link,
            "is_read": n.is_read
        })

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return JsonResponse({
        "notifications": data,
        "unread_count": unread_count
    })

@login_required
@csrf_exempt
def mark_notification_read(request, id):
    try:
        notification = Notification.objects.get(id=id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"status": "success"})
    except:
        return JsonResponse({"status": "error"})

def view_profile(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    return render(request, 'accounts/view_profile.html', {
        'profile_user': user_obj
    })

def ban_user(request, user_id):
    if not request.user.is_staff:
        return redirect('home')

    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()

    messages.success(request, "User has been banned successfully.")

    return redirect('view_profile', user_id=user.id)

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        users = User.objects.filter(email=email)

        if not users.exists():
            messages.error(request, "Email not registered.")
            return redirect("forgot_password")

        # Save email in session
        request.session["reset_email"] = email

        # If only ONE user → skip selection
        if users.count() == 1:
            user = users.first()
            request.session["reset_user"] = user.id
            return redirect("send_reset_otp")

        # If multiple users → show selection page
        request.session["reset_email"] = email
        return redirect("select_account_page")
    return render(request, "accounts/forgot_password.html")

def select_account(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")

        if not user_id:
            messages.error(request, "Please select an account.")
            return redirect("select_account_page")

        request.session["reset_user"] = int(user_id)
        request.session.modified = True

        return redirect("send_reset_otp")

    return redirect("select_account_page")
    
def verify_reset_otp(request):
    if request.method == "POST":
        otp_entered = request.POST.get("otp")
        user_id = request.session.get("reset_user")

        if not user_id:
            messages.error(request, "Session expired.")
            return redirect("forgot_password")

        user = User.objects.get(id=user_id)

        try:
            otp_obj = EmailOTP.objects.get(user=user)
        except EmailOTP.DoesNotExist:
            messages.error(request, "No OTP found.")
            return redirect("forgot_password")

        # ✅ EXPIRY CHECK
        if timezone.now() > otp_obj.created_at + timedelta(minutes=5):
            messages.error(request, "OTP expired.")
            return redirect("forgot_password")

        if otp_obj.otp != otp_entered:
            messages.error(request, "Invalid OTP.")
            return redirect("verify_reset_otp")

        request.session["otp_verified"] = True
        return redirect("reset_password")

    return render(request, "accounts/verify_reset_otp.html")

def reset_password(request):
    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password")

        user_id = request.session.get("reset_user")
        otp_verified = request.session.get("otp_verified")

        if not user_id or not otp_verified:
            messages.error(request, "Unauthorized access.")
            return redirect("forgot_password")

        user = User.objects.get(id=user_id)

        # ✅ CORRECT METHOD
        user.set_password(password)
        user.save()

        # ✅ CLEAN SESSION
        request.session.flush()

        messages.success(request, "Password reset successful. Please login.")
        return redirect("login")

    return render(request, "accounts/reset_password.html")

@login_required
def change_password(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        user = request.user

        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
            return redirect("change_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("change_password")

        user.set_password(new_password)
        user.save()

        messages.success(request, "Password changed successfully. Please login again.")
        return redirect("login")

    return render(request, "accounts/change_password.html")

def send_reset_otp(request):
    user_id = request.session.get("reset_user")

    if not user_id:
        messages.error(request, "Session expired.")
        return redirect("forgot_password")

    user = User.objects.get(id=user_id)

    otp = str(random.randint(100000, 999999))

    EmailOTP.objects.update_or_create(
        user=user,
        defaults={
            "otp": otp,
            "created_at": timezone.now()  # ✅ FORCE UPDATE TIME
        }
    )

    send_mail(
        subject="Pocket Job - Password Reset OTP",
        message=f"Your OTP is {otp}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    messages.success(request, f"OTP sent to {user.email}")
    return redirect("verify_reset_otp")

def select_account_page(request):
    email = request.session.get("reset_email")

    if not email:
        return redirect("forgot_password")

    users = User.objects.filter(email=email)

    return render(request, "accounts/select_account.html", {
        "users": users
    })
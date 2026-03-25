from django.shortcuts import render, redirect
from django.contrib.auth.models import User
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

            try:
                if user.profile.role == "APPLICANT":
                    return redirect("home")
                elif user.profile.role == "RECRUITER":
                    return redirect("home")
            except:
                return redirect("home")

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

        # Create user
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"]
        )

        # Create Profile
        profile = Profile.objects.create(
            user=user,
            role=data["role"]
        )

        # Restore uploaded image from session
        profile_pic_name = request.session.get("profile_pic_name")
        profile_pic_file = request.session.get("profile_pic_file")

        if profile_pic_name and profile_pic_file:
            image_file = ContentFile(
                profile_pic_file.encode("latin1"),
                name=profile_pic_name
            )
            profile.profile_pic.save(profile_pic_name, image_file, save=True)

        # Clear session
        request.session.pop("register_otp", None)
        request.session.pop("register_data", None)
        request.session.pop("profile_pic_name", None)
        request.session.pop("profile_pic_file", None)

        login(request, user)

        if data["role"] == "APPLICANT":
            return redirect("home")
        elif data["role"] == "RECRUITER":
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
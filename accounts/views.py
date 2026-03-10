from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.conf import settings
from django.core.files.base import ContentFile
from .models import Profile
import random


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
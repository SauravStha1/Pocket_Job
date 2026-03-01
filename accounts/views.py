from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.conf import settings
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
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


# =========================
# STEP 1: REGISTER VIEW - ENTER INFO & SEND OTP
# =========================
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect("register")

        otp = random.randint(100000, 999999)

        # Save registration info and OTP in session
        request.session["register_data"] = {
            "username": username,
            "email": email,
            "password": password
        }
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

        # Clear session
        del request.session["register_otp"]
        del request.session["register_data"]

        messages.success(request, "Account created successfully. You are now logged in.")
        login(request, user)
        return redirect("home")

    return render(request, "accounts/verify_otp.html")
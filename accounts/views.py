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
# REGISTER VIEW WITH OTP (FIXED VERSION)
# =========================
def register(request):
    if request.method == "POST":

        # =========================
        # STEP 1: SEND OTP
        # =========================
        if "send_otp" in request.POST:
            username = request.POST.get("username")
            email = request.POST.get("email")

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect("register")

            otp = random.randint(100000, 999999)

            # Store only non-sensitive data in session
            request.session["register_otp"] = str(otp)
            request.session["register_data"] = {
                "username": username,
                "email": email,
            }

            # Send OTP Email
            send_mail(
                subject="Pocket Job - OTP Verification",
                message=f"Your OTP code is {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(request, "OTP has been sent to your email.")
            return redirect("register")

        # =========================
        # STEP 2: VERIFY OTP & CREATE USER
        # =========================
        if "verify_otp" in request.POST:
            otp_entered = request.POST.get("otp")
            password = request.POST.get("password")  # Get password again securely
            session_otp = request.session.get("register_otp")
            data = request.session.get("register_data")

            if not session_otp or not data:
                messages.error(request, "Session expired. Please try again.")
                return redirect("register")

            if otp_entered != session_otp:
                messages.error(request, "Invalid OTP.")
                return redirect("register")

            if not password:
                messages.error(request, "Password cannot be empty.")
                return redirect("register")

            # Create user with fresh password
            User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=password
            )

            # Clear session
            del request.session["register_otp"]
            del request.session["register_data"]

            messages.success(request, "Account created successfully. Please login.")
            return redirect("login")

    return render(request, "accounts/register.html")
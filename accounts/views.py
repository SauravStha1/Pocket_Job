import random
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login

from .models import EmailOTP


def role_select(request):
    return render(request, 'accounts/role_select.html')


def applicant_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')

        return render(request, 'accounts/applicant_login.html', {
            'error': 'Invalid credentials'
        })

    return render(request, 'accounts/applicant_login.html')


def recruiter_login(request):
    return render(request, 'accounts/recruiter_login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/register.html', {
                'error': 'Username already exists'
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False
        )

        otp = str(random.randint(100000, 999999))

        EmailOTP.objects.create(user=user, otp=otp)

        send_mail(
            'Pocket Job OTP Verification',
            f'Your OTP is {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False
        )

        request.session['user_id'] = user.id
        return redirect('verify_otp')

    return render(request, 'accounts/register.html')



def verify_otp(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('register')

    user = User.objects.get(id=user_id)
    otp_obj = EmailOTP.objects.get(user=user)

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        if entered_otp == otp_obj.otp:
            user.is_active = True
            user.save()
            otp_obj.delete()
            return redirect('applicant_login')

        return render(request, 'accounts/verify_otp.html', {
            'error': 'Invalid OTP'
        })

    return render(request, 'accounts/verify_otp.html')

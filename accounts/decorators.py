from django.shortcuts import redirect
from django.contrib import messages


# ============================
# ADMIN REQUIRED
# ============================
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect("login")

        if request.user.profile.role != "ADMIN":
            messages.error(request, "Admin access required.")
            return redirect("home")

        return view_func(request, *args, **kwargs)
    return wrapper


# ============================
# RECRUITER REQUIRED
# ============================
def recruiter_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect("login")

        if request.user.profile.role != "RECRUITER":
            messages.error(request, "Recruiter access required.")
            return redirect("home")

        return view_func(request, *args, **kwargs)
    return wrapper


# ============================
# APPLICANT REQUIRED
# ============================
def applicant_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect("login")

        if request.user.profile.role != "APPLICANT":
            messages.error(request, "Applicant access required.")
            return redirect("home")

        return view_func(request, *args, **kwargs)
    return wrapper
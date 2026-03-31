from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


# ============================
# ADMIN ONLY
# ============================
class AdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.profile.role == "ADMIN"

    def handle_no_permission(self):
        messages.error(self.request, "Admin access required.")
        return redirect("home")


# ============================
# RECRUITER ONLY
# ============================
class RecruiterOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.profile.role == "RECRUITER"

    def handle_no_permission(self):
        messages.error(self.request, "Recruiter access required.")
        return redirect("home")


# ============================
# APPLICANT ONLY
# ============================
class ApplicantOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.profile.role == "APPLICANT"

    def handle_no_permission(self):
        messages.error(self.request, "Applicant access required.")
        return redirect("home")
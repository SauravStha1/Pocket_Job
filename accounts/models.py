from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):

    ROLE_CHOICES = (
        ('APPLICANT', 'Applicant'),
        ('RECRUITER', 'Recruiter'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Profile Picture
    profile_pic = models.ImageField(
        upload_to='profile_pics/',
        default='profile_pics/default_profile.png',
        blank=True,
        null=True
    )

    # =========================
    # APPLICANT FIELDS
    # =========================

    full_name = models.CharField(max_length=200, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    cv = models.FileField(upload_to='cv/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # =========================
    # RECRUITER FIELDS
    # =========================

    company_name = models.CharField(max_length=200, blank=True, null=True)
    owner_name = models.CharField(max_length=200, blank=True, null=True)
    company_location = models.CharField(max_length=200, blank=True, null=True)
    company_type = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company_email = models.EmailField(blank=True, null=True)
    founded_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
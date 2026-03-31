from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User



class Profile(models.Model):

    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),          # ✅ NEW
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


# =========================
# 🔔 NOTIFICATION MODEL
# =========================

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    notification_type = models.CharField(max_length=50)
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}"
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        from .models import Profile
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
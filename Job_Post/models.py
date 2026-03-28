from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

class Job(models.Model):

    JOB_TYPE_CHOICES = [
        ('Part Time', 'Part Time'),
        ('Full Time', 'Full Time'),
        ('Flexible', 'Flexible'),
    ]

    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='jobs'
    )

    title = models.CharField(max_length=200)
    tags = models.CharField(max_length=200)

    location = models.CharField(max_length=255, default="Unknown")

    job_type = models.CharField(
        max_length=50,
        choices=JOB_TYPE_CHOICES,
        default='Full Time'
    )

    min_salary = models.IntegerField(null=True, blank=True)
    max_salary = models.IntegerField(null=True, blank=True)
    negotiable = models.BooleanField(default=False)

    description = models.TextField()
    responsibilities = models.TextField()

    image = models.ImageField(
        upload_to='job_images/',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    deadline = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.deadline:
            self.deadline = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# =============================
# Job Application Model
# =============================
class JobApplication(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('HIRED', 'Hired'),
        ('REJECTED', 'Rejected'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey('accounts.Profile', on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    def __str__(self):
        return f"{self.applicant.user.username} → {self.job.title}"
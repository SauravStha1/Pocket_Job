from django.db import models
from django.contrib.auth.models import User


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

    # NEW FIELD: Job Image (Optional)
    image = models.ImageField(
        upload_to='job_images/',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)  # Soft delete support

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
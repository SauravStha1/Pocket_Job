from django.db import models

class Job(models.Model):

    JOB_TYPE_CHOICES = [
        ('Part Time', 'Part Time'),
        ('Full Time', 'Full Time'),
        ('Flexible', 'Flexible'),
    ]

    title = models.CharField(max_length=200)
    tags = models.CharField(max_length=200)

    job_type = models.CharField(
        max_length=50,
        choices=JOB_TYPE_CHOICES,
        default='Full Time'   # 👈 THIS FIXES MIGRATION ERROR
    )

    min_salary = models.IntegerField(null=True, blank=True)
    max_salary = models.IntegerField(null=True, blank=True)
    negotiable = models.BooleanField(default=False)

    description = models.TextField()
    responsibilities = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

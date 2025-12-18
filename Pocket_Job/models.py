from django.db import models

class Job(models.Model):

    JOB_ROLE_CHOICES = [
        ('Barista', 'Barista'),
        ('Junior Barista', 'Junior Barista'),
        ('Trainer', 'Trainer'),
    ]

    title = models.CharField(max_length=200)
    tags = models.CharField(max_length=200)
    job_role = models.CharField(max_length=100, choices=JOB_ROLE_CHOICES)

    min_salary = models.IntegerField()
    max_salary = models.IntegerField()
    negotiable = models.BooleanField(default=False)

    description = models.TextField()
    responsibilities = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

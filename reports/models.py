from django.db import models
from django.conf import settings

class Report(models.Model):
    REPORT_TYPE = (
        ('job', 'Job'),
        ('user', 'User'),
    )

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE)

    job = models.ForeignKey(
        'Job_Post.Job', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='reported_user'
    )

    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = self.job.title if self.report_type == 'job' else self.reported_user.username
        return f"{self.reporter.username} reported {self.report_type}: {target}"
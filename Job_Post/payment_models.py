from django.db import models
from django.contrib.auth.models import User
from .models import Job
import uuid


class Payment(models.Model):

    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.IntegerField(default=1000)

    # Unique transaction id required by eSewa
    transaction_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Job {self.job.id} - {self.status}"
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

    PAYMENT_METHODS = [
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
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

    amount = models.PositiveIntegerField(default=1000)  # ✅ better than IntegerField

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='esewa'
    )

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

    # ✅ NEW (VERY USEFUL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # newest first

    def __str__(self):
        return f"{self.payment_method} | Job {self.job.id} | {self.status}"

    # ✅ OPTIONAL HELPER (nice for later use)
    def is_success(self):
        return self.status == "COMPLETED"
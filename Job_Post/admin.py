from django.contrib import admin
from .models import Job
from .payment_models import Payment


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'recruiter', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'recruiter__username')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'recruiter', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('recruiter__username',)
from django.shortcuts import render
from Job_Post.models import Job


def home(request):
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'homepage/home.html', {
        'jobs': jobs
    })

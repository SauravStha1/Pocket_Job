from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from Job_Post.models import Job

@login_required
def home(request):
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'homepage/home.html', {'jobs': jobs})

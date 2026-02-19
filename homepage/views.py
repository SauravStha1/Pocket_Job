from django.shortcuts import render
from django.db.models import Q
from Job_Post.models import Job

def home(request):
    query = request.GET.get('q')
    job_type = request.GET.get('job_type')

    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | Q(tags__icontains=query)
        )

    if job_type and job_type != "All":
        jobs = jobs.filter(job_type=job_type)

    jobs = jobs.order_by('-created_at')

    return render(request, 'homepage/home.html', {
        'jobs': jobs,
        'query': query,
        'selected_job_type': job_type
    })

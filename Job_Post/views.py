from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from .forms import JobForm

def job_list(request):
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'Job_Post/job_list.html', {'jobs': jobs})

def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('job_list')  # 👈 redirect to home page
    else:
        form = JobForm()

    return render(request, 'Job_Post/job_form.html', {'form': form})

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'Job_Post/job_detail.html', {'job': job})

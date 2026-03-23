from django.shortcuts import render
from django.db.models import Q
from Job_Post.models import Job


def home(request):
    query = request.GET.get('q')
    job_type = request.GET.get('job_type')

    jobs = Job.objects.filter(is_active=True)

    # Apply search filters
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | Q(tags__icontains=query)
        )

    if job_type and job_type != "All":
        jobs = jobs.filter(job_type=job_type)

    # ==============================
    # 🎯 SKILL-BASED FILTER (SEARCH STYLE)
    # ==============================
    if request.user.is_authenticated:
        profile = request.user.profile
        skills = profile.skills

        if skills:
            skill_list = [s.strip().lower() for s in skills.split(",")]

            # Step 1: Find matching jobs
            matched_jobs = []
            other_jobs = []

            for job in jobs:
                job_text = (job.title + " " + job.tags).lower()

                if any(skill in job_text for skill in skill_list):
                    matched_jobs.append(job)
                else:
                    other_jobs.append(job)

            # Step 2: Combine (like search result priority)
            jobs = matched_jobs + other_jobs

    else:
        jobs = list(jobs.order_by('-created_at'))

    return render(request, 'homepage/home.html', {
        'jobs': jobs,
        'query': query,
        'selected_job_type': job_type
    })
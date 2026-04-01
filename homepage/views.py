from django.shortcuts import redirect, render
from django.db.models import Q
from django.core.paginator import Paginator
from Job_Post.models import Job
from django.contrib.auth.models import User


def home(request):
    query = request.GET.get('q')
    job_type = request.GET.get('job_type')

    jobs = Job.objects.filter(is_active=True)

    # ── Search filters ──
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(tags__icontains=query) |
            Q(location__icontains=query)
        )

    if job_type and job_type != "All":
        jobs = jobs.filter(job_type=job_type)

    # ── Skill-based prioritisation ──
    recommended_ids = []

    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)

        if profile and profile.skills:
            skill_list = [s.strip().lower() for s in profile.skills.split(",")]

            matched_jobs = []
            other_jobs = []

            for job in jobs:
                job_text = (job.title + " " + job.tags).lower()

                if any(skill in job_text for skill in skill_list):
                    matched_jobs.append(job)
                    recommended_ids.append(job.id)
                else:
                    other_jobs.append(job)

            jobs = matched_jobs + other_jobs
        else:
            jobs = list(jobs.order_by('-created_at'))
    else:
        jobs = list(jobs.order_by('-created_at'))

    # ── Pagination ──
    paginator = Paginator(jobs, 24)
    page_number = request.GET.get('page')
    jobs_page = paginator.get_page(page_number)

    # ── Stats ──
    total_jobs = Job.objects.filter(is_active=True).count()

    total_companies = (
        Job.objects.filter(is_active=True)
        .values('recruiter')
        .distinct()
        .count()
    )

    # Safe applicant count
    try:
        from accounts.models import Profile
        total_applicants = Profile.objects.filter(role='APPLICANT').count()
    except Exception:
        total_applicants = User.objects.filter(
            is_staff=False,
            is_superuser=False
        ).count()

    return render(request, 'homepage/home.html', {
        'jobs': jobs_page,
        'query': query,
        'selected_job_type': job_type,
        'recommended_ids': recommended_ids,

        # Stats
        'total_jobs': total_jobs,
        'total_companies': total_companies,
        'total_applicants': total_applicants,
    })
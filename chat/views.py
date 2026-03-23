from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Case, When, IntegerField
from Job_Post.models import Job, JobApplication
from .models import ChatRoom, Message


# 🔥 GLOBAL UNREAD COUNT FUNCTION
def get_unread_count(user):
    return Message.objects.filter(
        chatroom__in=ChatRoom.objects.filter(
            Q(recruiter=user) | Q(applicant=user)
        ),
        is_read=False
    ).exclude(sender=user).count()


# ----------------------------
# Recruiter starts a chat
# ----------------------------
@login_required
def start_chat(request, application_id, job_id):
    recruiter = request.user
    application = get_object_or_404(JobApplication, id=application_id)
    applicant = application.applicant.user
    job = get_object_or_404(Job, id=job_id)

    chatroom, created = ChatRoom.objects.get_or_create(
        recruiter=recruiter,
        applicant=applicant,
        job=job
    )

    return redirect('chat_room', chatroom_id=chatroom.id)


# ----------------------------
# Chat room view
# ----------------------------
@login_required
def chat_room(request, chatroom_id):
    chatroom = get_object_or_404(ChatRoom, id=chatroom_id)

    if request.user != chatroom.recruiter and request.user != chatroom.applicant:
        return redirect('home')

    # 🔥 MARK AS READ WHEN OPENED
    Message.objects.filter(
        chatroom=chatroom,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    messages = chatroom.messages.all().order_by('timestamp')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            if request.user.profile.role == "APPLICANT" and messages.count() == 0:
                pass
            else:
                Message.objects.create(
                    chatroom=chatroom,
                    sender=request.user,
                    content=content
                )
                return redirect('chat_room', chatroom_id=chatroom.id)

    return render(request, 'chat/chat_room.html', {
        'chatroom': chatroom,
        'messages': messages,
        'unread_count': get_unread_count(request.user)  # 🔥 for navbar
    })


# ----------------------------
# Applicant chats
# ----------------------------
@login_required
def my_chats(request):
    if request.user.profile.role != "APPLICANT":
        return redirect('home')

    chatrooms = ChatRoom.objects.filter(applicant=request.user).order_by('-created_at')

    return render(request, 'chat/my_chats.html', {
        'chatrooms': chatrooms,
        'unread_count': get_unread_count(request.user)
    })


# ----------------------------
# Inbox
# ----------------------------
@login_required
def inbox(request):
    user = request.user
    role = user.profile.role

    if role == "RECRUITER":
        chatrooms = ChatRoom.objects.filter(recruiter=user).select_related('applicant', 'job')
    else:
        chatrooms = ChatRoom.objects.filter(applicant=user).select_related('recruiter', 'job')

    # 🔥 ADD UNREAD PRIORITY
    chatrooms = chatrooms.annotate(
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=user)
        )
    ).annotate(
        unread_priority=Case(
            When(unread_count__gt=0, then=0),
            default=1,
            output_field=IntegerField()
        )
    ).order_by('unread_priority', '-created_at')

    context = {
        'chatrooms': chatrooms,
        'role': role,
        'unread_count': get_unread_count(user)
    }

    if role == "APPLICANT":
        applications = JobApplication.objects.filter(applicant=user.profile)
        pending_apps = [app for app in applications if not chatrooms.filter(job=app.job).exists()]
        context['pending_apps'] = pending_apps

    return render(request, 'chat/inbox.html', context)
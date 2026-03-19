from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from Job_Post.models import Job, JobApplication
from .models import ChatRoom, Message

# ----------------------------
# Recruiter starts a chat with an applicant
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

    # Security: only recruiter or applicant can access
    if request.user != chatroom.recruiter and request.user != chatroom.applicant:
        return redirect('home')

    messages = chatroom.messages.all().order_by('timestamp')

    # Only for non-WebSocket POST (optional)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            # Applicant cannot send first message
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
        'messages': messages
    })


# ----------------------------
# Applicant: view all active chats
# ----------------------------
@login_required
def my_chats(request):
    if request.user.profile.role != "APPLICANT":
        return redirect('home')

    chatrooms = ChatRoom.objects.filter(applicant=request.user).order_by('-created_at')
    return render(request, 'chat/my_chats.html', {'chatrooms': chatrooms})


# ----------------------------
# Inbox: recruiter sees active chats + pending applicants
# ----------------------------
@login_required
def inbox(request):
    user = request.user
    role = user.profile.role

    if role == "RECRUITER":
        chatrooms = ChatRoom.objects.filter(recruiter=user).select_related('applicant', 'job').order_by('-created_at')
        return render(request, 'chat/inbox.html', {
            'chatrooms': chatrooms,
            'role': role
        })

    else:  # applicant inbox
        chatrooms = ChatRoom.objects.filter(applicant=user).select_related('recruiter', 'job').order_by('-created_at')
        # pending applications where recruiter has not started chat
        applications = JobApplication.objects.filter(applicant=user.profile)
        pending_apps = [app for app in applications if not chatrooms.filter(job=app.job).exists()]

        return render(request, 'chat/inbox.html', {
            'chatrooms': chatrooms,
            'pending_apps': pending_apps,
            'role': role
        })
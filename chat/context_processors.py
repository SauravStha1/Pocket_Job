from django.db.models import Q
from .models import Message, ChatRoom

def unread_messages(request):
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(
            chatroom__in=ChatRoom.objects.filter(
                Q(recruiter=request.user) | Q(applicant=request.user)
            ),
            is_read=False
        ).exclude(sender=request.user).count()

        return {'unread_count': unread_count}

    return {'unread_count': 0}
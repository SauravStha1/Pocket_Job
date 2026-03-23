from django.db import models
from django.contrib.auth.models import User
from Job_Post.models import Job

# Chat room connecting recruiter and applicant for a job
class ChatRoom(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recruiter_chats')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applicant_chats')
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recruiter.username} - {self.applicant.username} ({self.job.title})"


# Messages in a chat room
class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # 🔥 NEW FIELD
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"
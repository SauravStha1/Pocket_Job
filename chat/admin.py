from django.contrib import admin
from .models import ChatRoom, Message

# Inline messages inside a chatroom for easy viewing
class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'timestamp')
    can_delete = False

# ChatRoom admin
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'recruiter', 'applicant', 'created_at')
    inlines = [MessageInline]
    search_fields = ('job__title', 'recruiter__username', 'applicant__username')
    readonly_fields = ('created_at',)

# Message admin (optional, for direct access)
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chatroom', 'sender', 'content', 'timestamp')
    list_filter = ('chatroom', 'sender')
    search_fields = ('content',)
    readonly_fields = ('timestamp',)
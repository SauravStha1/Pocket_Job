import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chatroom_id = self.scope['url_route']['kwargs']['chatroom_id']
        self.room_group_name = f'chat_{self.chatroom_id}'

        # Add user to room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Remove from room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        user = self.scope['user']

        if not message:
            return  # ignore empty messages

        # Save message to DB
        msg_obj = await self.save_message(user, message)
        if not msg_obj:
            # business rule: applicant cannot send first message
            return

        # Broadcast to all in the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': msg_obj.content,
                'sender': user.username,
                'time': msg_obj.timestamp.strftime('%H:%M')
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    # ----------------------------
    # Database save (sync to async)
    # ----------------------------
    @database_sync_to_async
    def save_message(self, user, message):
        chatroom = ChatRoom.objects.get(id=self.chatroom_id)

        # Business rule: applicant cannot send first message
        if user.profile.role == "APPLICANT" and chatroom.messages.count() == 0:
            return None

        return Message.objects.create(chatroom=chatroom, sender=user, content=message)
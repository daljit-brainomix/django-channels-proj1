import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .models import Room

# Since WebsocketConsumer is a synchronous consumer, we had to call async_to_sync when working with the channel layer. We decided to go with a
# sync consumer since the chat app is closely connected to Django (which is sync by default). In other words, we wouldn't get a performance
# boost by using an async consumer.
# You should use sync consumers by default. What's more, only use async consumers in cases where you're absolutely certain that you're
# doing something that would benefit from async handling (e.g., long-running tasks that could be done in parallel) and you're only using
# async-native libraries.
class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None

    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.room = Room.objects.get(name=self.room_name)

        # Connection has to be accepted
        self.accept()

        # join the room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )

    def receive(self, text_data=None, bytes_data=None):
        # Parse JSON data
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # send chat message event to the room
        # When using channel layer's group_send, your consumer has to have a method for every JSON message type you use.
        # In our situation, type is equaled to chat_message. Thus, we added a method called chat_message.
        # If you use dots in your message types, Channels will automatically convert them to underscores when looking for
        # a method -- e.g, chat.message will become chat_message.
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
            },
        )

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

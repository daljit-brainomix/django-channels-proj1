import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .models import Room, Message

# Since WebsocketConsumer is a synchronous consumer, we had to call async_to_sync when working with the channel layer. We decided to go with a
# sync consumer since the chat app is closely connected to Django (which is sync by default). In other words, we wouldn't get a performance
# boost by using an async consumer.
# You should use sync consumers by default. What's more, only use async consumers in cases where you're absolutely certain that you're
# doing something that would benefit from async handling (e.g., long-running tasks that could be done in parallel) and you're only using
# async-native libraries.

# WebsocketConsumer provides three methods, connect(), disconnect(), and receive():
class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.user_inbox = None

    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.room = Room.objects.get(name=self.room_name)
        # As we wrapped asgi.py/URLRouter in AuthMiddlewareStack, whenever an authenticated client joins,
        # the user object will be added to the scope. It can accessed like so: user = self.scope['user']
        self.user = self.scope["user"]
        # The Channels package doesn't allow direct filtering, so there's no built-in method for sending messages from a client to another client. With Channels you can either send a message to:
        # The consumer's client (self.send)
        # A channel layer group (self.channel_layer.group_send)
        # Thus, in order to implement private messaging, we'll:
        # Create a new group called inbox_%USERNAME% every time a client joins.
        # Add the client to their own inbox group (inbox_%USERNAME%).
        # Remove the client from their inbox group (inbox_%USERNAME%) when they disconnect.
        # Once implemented, each client will have their own inbox for private messages. Other clients can then send private messages to inbox_%TARGET_USERNAME%.
        self.user_inbox = f"inbox_{self.user.username}"

        # Connection has to be accepted
        self.accept()

        # join the room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

        # Send the user list to the newly joined user
        self.send(
            json.dumps(
                {
                    "type": "user_list",
                    "users": [user.username for user in self.room.online.all()],
                }
            )
        )

        if self.user.is_authenticated:
            # Send the user joined event to the room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "user_join",
                    "user": self.user.username,
                },
            )
            self.room.online.add(self.user)

            # Create a user inbox for private messages
            async_to_sync(self.channel_layer.group_add)(
                self.user_inbox,
                self.channel_name,
            )

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )

        if self.user.is_authenticated:
            # On Disconnect, delete the user inbox for private message
            async_to_sync(self.channel_layer.group_discard)(
                self.user_inbox,
                self.channel_name,
            )

            # send the user left event to the room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "user_leave",
                    "user": self.user.username,
                },
            )
            self.room.online.remove(self.user)

    def receive(self, text_data=None, bytes_data=None):
        # Parse JSON data
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        if not self.user.is_authenticated:
            return

        if message.startswith("/pm "):
            split = message.split(" ", 2)
            target = split[1]
            target_msg = split[2]

            # Send private message to the target
            async_to_sync(self.channel_layer.group_send)(
                f"inbox_{target}",
                {
                    "type": "private_message",
                    "user": self.user.username,
                    "message": target_msg,
                },
            )
            # Send private message delievered to the user
            self.send(
                json.dumps(
                    {
                        "type": "private_message_delivered",
                        "target": target,
                        "message": target_msg,
                    }
                )
            )
            return

        # send chat message event to the room
        # When using channel layer's group_send, your consumer has to have a method for every JSON message type you use.
        # In our situation, type is equaled to chat_message. Thus, we added a method called chat_message.
        # If you use dots in your message types, Channels will automatically convert them to underscores when looking for
        # a method -- e.g, chat.message will become chat_message.
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "chat_message",
                "user": self.user.username,
                "message": message,
            },
        )
        Message.objects.create(user=self.user, room=self.room, content=message)

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def user_join(self, event):
        self.send(text_data=json.dumps(event))

    def user_leave(self, event):
        self.send(text_data=json.dumps(event))

    def private_message(self, event):
        self.send(text_data=json.dumps(event))

    def private_message_delivered(self, event):
        self.send(text_data=json.dumps(event))

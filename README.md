Clone repo, install from requirements.txt, and do the migration

`(env)$ python manage.py migrate`

URLs:

host/chat/ - chat room selector

host/chat/<ROOM_NAME>/ - chat room


#### Redis

A channel layer is a kind of a communication system, which allows multiple parts of our application to exchange messages, without shuttling all the messages or events through the database. We need a channel layer to give consumers the ability to talk to one another.

While we could use use the InMemoryChannelLayer layer since we're in development mode, we'll use a production-ready layer, RedisChannelLayer. Since this layer requires Redis, run the following command to get it up and running with Docker:

(env)$ docker run -p 6379:6379 -d redis:5

To connect to Redis from Django, we need to install an additional package called channels_redis and update settings.py with config:

`(env)$ pip install channels_redis==3.3.1`


```
(env)$ python manage.py shell
>>> import channels.layers
>>> channel_layer = channels.layers.get_channel_layer()
>>>
>>> from asgiref.sync import async_to_sync
>>> async_to_sync(channel_layer.send)('test_channel', {'type': 'hello'})
>>> async_to_sync(channel_layer.receive)('test_channel')
{'type': 'hello'}
```

Here, we connected to the channel layer using the settings defined in core/settings.py. We then used channel_layer.send to send a message to the test_channel group and channel_layer.receive to read all the messages sent to the same group.

Take note that we wrapped all the function calls in async_to_sync because the channel layer is asynchronous.

Channels Consumer
A consumer is the basic unit of Channels code. They are tiny ASGI applications, driven by events. They are akin to Django views. However, unlike Django views, consumers are long-running by default. A Django project can have multiple consumers that are combined using Channels routing (which we'll take a look at in the next section).

Each consumer has it's own scope, which is a set of details about a single incoming connection. They contain pieces of data like protocol type, path, headers, routing arguments, user agent, and more.


TODO

Adding admin-only chat rooms.
Sending the last ten messages to the user when they join a chat room.
Allowing users to edit and delete messages.
Adding '{user} is typing' functionality.
Adding message reactions.
The ideas are ranked from the easiest to the hardest to implement.

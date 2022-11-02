from django.contrib import admin

from chat_app.models import Room, Message

admin.site.register(Room)
admin.site.register(Message)
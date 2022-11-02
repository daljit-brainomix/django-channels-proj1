from django.shortcuts import render

from chat_app.models import Room


def index_view(request):
    return render(
        request,
        "index.html",
        {
            "rooms": Room.objects.all(),
        },
    )


def room_view(request, room_name):
    chat_room, created = Room.objects.get_or_create(name=room_name)
    print(chat_room)
    return render(
        request,
        "room.html",
        {
            "room": chat_room,
        },
    )

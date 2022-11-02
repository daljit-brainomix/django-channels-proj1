from unittest.util import _MAX_LENGTH
from django.contrib.auth.models import User
from django.db import models

class Room(models.Model):
    name = models.CharField(max_length=128)
    online = models.ManyToManyField(to=User, blank=True)
    
    def get_online_count(self):
        return self.online.count()
    
    def join(self, user):
        return self.online.add(user)
    
    def leave(self, user):
        return self.online.remove(user)
    
    def __str__(self):
        return f"{self.name} ({self.get_online_count()})"
    
    
class Message(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    room = models.ForeignKey(to=Room, on_delete=models.CASCADE)
    content = models.CharField(max_length=512)
    timestamp = models.DateTimeField(auto_now_add=True)
    

    
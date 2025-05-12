from django.db import models

class User(models.Model):
    spotify_id = models.CharField(max_length=255, unique=True)
    access_token = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song_id = models.CharField(max_length=255)
    rating = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    mood = models.CharField(max_length=50, choices=[
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('relaxed', 'Relaxed'),
        ('angry', 'Angry'),
        ('excited', 'Excited'),
    ])
    
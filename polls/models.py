from django.db import models
from django.conf import settings

# Create your models here.

class Poll(models.Model):
    url = models.URLField()
    name = models.TextField(blank=True)
    description = models.TextField(blank=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    is_open = models.BooleanField(default=True)
    result = models.PositiveIntegerField(default=0)

class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    poll = models.ForeignKey('polls.Poll', related_name='votes', on_delete=models.CASCADE)
    weight = models.PositiveSmallIntegerField(default=1)
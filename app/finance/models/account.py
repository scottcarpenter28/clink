import uuid
from django.db import models
from django.contrib.auth.models import User


class Account(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    starting_balance = models.FloatField(default=0.0)
    name = models.CharField(max_length=64)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_account'
        ordering = ['-created']

    def __str__(self):
        return f"{self.name} ({self.owner.username})"

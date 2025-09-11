import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from .account import Account
from .category import Category


class Transaction(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions')
    amount = models.FloatField(validators=[MinValueValidator(0.01)])
    vendor = models.CharField(max_length=32, default='')
    transaction_date = models.DateField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-created']

    def __str__(self):
        return f"{self.category.name}: ${self.amount} - {self.account.name}"

import uuid
from django.db import models
from django.core.validators import MinValueValidator

from .account import Account
from .category import Category


class IncomeOrExpense(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions')
    amount = models.FloatField(validators=[MinValueValidator(0.01)])
    vendor = models.CharField(max_length=32, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_income_or_expense'
        ordering = ['-created']

    def __str__(self):
        return f"{self.category.name}: ${self.amount} - {self.account.name}"

from django.db import models
from .account import Account


class AccountTracker(models.Model):
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='balance_history')
    balance = models.FloatField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_account_tracker'
        ordering = ['-created']

    def __str__(self):
        return f"{self.account.name} - Balance: ${self.balance}"

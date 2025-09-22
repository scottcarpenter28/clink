import uuid
from django.db import models
from django.contrib.auth.models import User


class Budget(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    month = models.DateField()  # Store the first day of the month
    total_income = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_budget'
        ordering = ['-month']
        constraints = [
            models.UniqueConstraint(fields=['user', 'month'], name='unique_user_month_budget')
        ]

    def __str__(self):
        return f"Budget for {self.month.strftime('%B %Y')} - {self.user.username}"

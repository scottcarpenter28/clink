import uuid
from django.db import models
from django.db.models import Sum
from datetime import timedelta
from .budget import Budget
from .category import Category
from .transaction import Transaction


class BudgetAllocation(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='allocations')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budget_allocations')
    allocated_amount = models.FloatField(default=0.0)
    rollover_from_previous = models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_budget_allocation'
        ordering = ['category__name']
        constraints = [
            models.UniqueConstraint(fields=['budget', 'category'], name='unique_budget_category')
        ]

    def __str__(self):
        return f"{self.category.name}: ${self.allocated_amount} - {self.budget}"

    @property
    def spent_amount(self):
        """Calculate the amount spent in this category for the budget month."""
        # Get month start and end date
        month_start = self.budget.month
        # Get the next month's first day
        next_month = month_start.replace(day=28) + timedelta(days=4)
        month_end = next_month.replace(day=1) - timedelta(days=1)

        # Get sum of transactions for this category in the budget's month
        spent = Transaction.objects.filter(
            category=self.category,
            transaction_date__gte=month_start,
            transaction_date__lte=month_end,
            account__owner=self.budget.user
        ).aggregate(total=Sum('amount'))['total'] or 0

        return spent

    @property
    def remaining_amount(self):
        """Calculate the remaining amount in the budget."""
        total_available = self.allocated_amount + self.rollover_from_previous
        return total_available - self.spent_amount

    @property
    def percent_spent(self):
        """Calculate the percentage of budget spent."""
        total_available = self.allocated_amount + self.rollover_from_previous
        if total_available == 0:
            return 0
        return (self.spent_amount / total_available) * 100

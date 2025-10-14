from django.db import models
from django.core.exceptions import ValidationError
from finance.models.base_financial_model import BaseFinancialModel
from finance.enums import TransactionType
from typing import override


class Budget(BaseFinancialModel):
    budget_year: models.PositiveIntegerField = models.PositiveIntegerField(
        blank=False, null=False, default=2025
    )

    budget_month: models.PositiveIntegerField = models.PositiveIntegerField(
        blank=False, null=False, default=1
    )

    allow_carry_over: models.BooleanField = models.BooleanField(
        blank=False, null=False, default=False
    )

    carried_over_amount_in_cents: models.PositiveIntegerField = (
        models.PositiveIntegerField(blank=False, null=False, default=0)
    )

    def clean(self) -> None:
        super().clean()
        if self.budget_month < 1 or self.budget_month > 12:
            raise ValidationError({"budget_month": "Month must be between 1 and 12."})

    @override
    def __str__(self) -> str:
        return f"Budget: {self.category} - ${self.amount_dollars:.2f} ({self.type}) - {self.budget_year}/{self.budget_month:02d}"

    class Meta:
        ordering = ["-budget_year", "-budget_month", "-date_created"]
        unique_together = [["user", "category", "type", "budget_year", "budget_month"]]

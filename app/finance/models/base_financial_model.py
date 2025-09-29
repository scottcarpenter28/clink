from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from typing import Any
from finance.enums import TransactionType


class BaseFinancialModel(models.Model):
    TYPE_CHOICES: list[tuple[str, str]] = [
        (TransactionType.INCOME.name, TransactionType.INCOME.value),
        (TransactionType.NEED.name, TransactionType.NEED.value),
        (TransactionType.WANT.name, TransactionType.WANT.value),
        (TransactionType.DEBTS.name, TransactionType.DEBTS.value),
        (TransactionType.SAVINGS.name, TransactionType.SAVINGS.value),
        (TransactionType.INVESTING.name, TransactionType.INVESTING.value),
    ]

    user: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=False, null=False
    )

    type: models.CharField = models.CharField(
        max_length=20, choices=TYPE_CHOICES, blank=False, null=False
    )

    category: models.CharField = models.CharField(
        max_length=100, blank=False, null=False
    )

    amount_in_cents: models.PositiveIntegerField = models.PositiveIntegerField(
        blank=False, null=False
    )

    date_created: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    date_updated: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def amount_dollars(self) -> float:
        return float(self.amount_in_cents or 0) / 100

    @classmethod
    def from_dollars(
        cls, dollar_amount: float, **kwargs: dict[str, Any]
    ) -> models.Model:
        cents = int(abs(dollar_amount) * 100)
        return cls(amount_in_cents=cents, **kwargs)

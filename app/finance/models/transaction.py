from django.db import models
from finance.models.base_financial_model import BaseFinancialModel
from finance.enums import TransactionType
from typing import override


class Transaction(BaseFinancialModel):
    date_of_expense: models.DateField = models.DateField(blank=False, null=False)

    @override
    def __str__(self) -> str:
        return f"{self.category} - ${self.amount_dollars:.2f} ({self.date_of_expense})"

    class Meta:
        ordering = ["-date_of_expense"]

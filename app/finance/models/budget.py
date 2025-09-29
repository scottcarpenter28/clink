from django.db import models
from finance.models.base_financial_model import BaseFinancialModel
from finance.enums import TransactionType
from typing import override


class Budget(BaseFinancialModel):
    @override
    def __str__(self) -> str:
        return f"Budget: {self.category} - ${self.amount_dollars:.2f} ({self.type})"

    class Meta:
        ordering = ["-date_created"]

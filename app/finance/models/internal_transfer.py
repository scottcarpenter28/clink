from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from finance.models.budget import Budget


class InternalTransfer(models.Model):
    user: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=False, null=False
    )

    source_budget: models.ForeignKey = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="outgoing_transfers",
        blank=False,
        null=False,
    )

    destination_budget: models.ForeignKey = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="incoming_transfers",
        blank=True,
        null=True,
    )

    amount_in_cents: models.PositiveIntegerField = models.PositiveIntegerField(
        blank=False, null=False
    )

    transfer_date: models.DateField = models.DateField(blank=False, null=False)

    description: models.CharField = models.CharField(
        max_length=255, blank=True, null=False, default=""
    )

    date_created: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    date_updated: models.DateTimeField = models.DateTimeField(auto_now=True)

    @property
    def amount_dollars(self) -> float:
        return float(self.amount_in_cents or 0) / 100

    def clean(self) -> None:
        super().clean()

        if self.amount_in_cents <= 0:
            raise ValidationError(
                {"amount_in_cents": "Transfer amount must be greater than 0."}
            )

        if self.source_budget.type == "INCOME":
            raise ValidationError(
                {"source_budget": "Cannot transfer from INCOME type budgets."}
            )

        if self.source_budget == self.destination_budget:
            raise ValidationError("Source and destination budgets cannot be the same.")

    def __str__(self) -> str:
        destination = (
            self.destination_budget.category
            if self.destination_budget
            else "Used Funds"
        )
        return f"Transfer: {self.source_budget.category} → {destination} - ${self.amount_dollars:.2f} on {self.transfer_date}"

    class Meta:
        ordering = ["-transfer_date", "-date_created"]
        indexes = [
            models.Index(fields=["source_budget"]),
            models.Index(fields=["destination_budget"]),
        ]

from decimal import Decimal
from datetime import date

from django import forms

from finance.models.transaction import Transaction
from finance.enums import TransactionType


class TransactionForm(forms.ModelForm):
    amount = forms.DecimalField(decimal_places=2, min_value=0.01, required=True)

    class Meta:
        model = Transaction
        fields = ["type", "category", "amount", "date_of_expense"]
        widgets = {
            "date_of_expense": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_amount(self) -> Decimal:
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean_type(self) -> str:
        type_value = self.cleaned_data.get("type")
        valid_types = [t.name for t in TransactionType]
        if type_value not in valid_types:
            raise forms.ValidationError("Invalid transaction type.")
        return type_value

    def clean_date_of_expense(self) -> date:
        date_of_expense = self.cleaned_data.get("date_of_expense")
        return date_of_expense

    def save(self, commit: bool = True) -> Transaction:
        instance = super().save(commit=False)
        amount_dollars = self.cleaned_data["amount"]
        instance.amount_in_cents = int(float(amount_dollars) * 100)
        if commit:
            instance.save()
        return instance

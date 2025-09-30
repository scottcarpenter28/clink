from typing import TypedDict, Any, Dict
from decimal import Decimal

from django import forms
from django.contrib.auth.models import User
from django.forms import formset_factory

from finance.models import Budget
from finance.enums import TransactionType


class BudgetItemData(TypedDict):
    type: str
    category: str
    amount: float | Decimal


class FormsetData(TypedDict):
    pass


class CleanedFormData(TypedDict):
    type: str
    category: str
    amount: Decimal
    DELETE: bool


class BudgetItemForm(forms.Form):
    type = forms.ChoiceField(
        choices=[(t.name, t.value) for t in TransactionType], required=True
    )
    category = forms.CharField(max_length=100, required=True)
    amount = forms.DecimalField(decimal_places=2, required=True)

    def clean_amount(self) -> Decimal:
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount

    def clean_type(self) -> str:
        type_value = self.cleaned_data.get("type")
        valid_types = [t.name for t in TransactionType]
        if type_value not in valid_types:
            raise forms.ValidationError("Invalid transaction type.")
        return type_value


BudgetItemFormSet = formset_factory(
    BudgetItemForm, extra=0, min_num=1, validate_min=True
)


class MultiBudgetForm(forms.Form):
    year = forms.IntegerField(min_value=1900, required=True)
    month = forms.IntegerField(min_value=1, max_value=12, required=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.formset = None
        if "data" in kwargs or (args and args[0] is not None):
            data = kwargs.get("data") or args[0]
            if data and "budgets" in data:
                formset_data = self._prepare_formset_data(data["budgets"])
                self.formset = BudgetItemFormSet(formset_data)
            else:
                self.formset = BudgetItemFormSet()

    def _prepare_formset_data(
        self, budgets_list: list[BudgetItemData]
    ) -> Dict[str, str]:
        formset_data = {
            "form-TOTAL_FORMS": str(len(budgets_list)),
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "1",
            "form-MAX_NUM_FORMS": "1000",
        }
        for idx, budget in enumerate(budgets_list):
            formset_data[f"form-{idx}-type"] = budget.get("type", "")
            formset_data[f"form-{idx}-category"] = budget.get("category", "")
            formset_data[f"form-{idx}-amount"] = str(budget.get("amount", ""))
        return formset_data

    def is_valid(self) -> bool:
        form_valid = super().is_valid()
        formset_valid = self.formset.is_valid() if self.formset else False
        return form_valid and formset_valid

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()

        if self.formset and self.formset.is_valid():
            categories_types: set[tuple[str, str]] = set()
            for form in self.formset:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    category = form.cleaned_data.get("category")
                    type_value = form.cleaned_data.get("type")
                    combo = (category, type_value)
                    if combo in categories_types:
                        raise forms.ValidationError(
                            f"Duplicate entry found: {category} ({type_value}). "
                            "Each category-type combination must be unique."
                        )
                    categories_types.add(combo)

        return cleaned_data

    def save(self, user: User) -> list[Budget]:
        if not self.is_valid():
            raise ValueError("Cannot save invalid form")

        year: int = self.cleaned_data["year"]
        month: int = self.cleaned_data["month"]
        created_budgets: list[Budget] = []

        for form in self.formset:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                type_value: str = form.cleaned_data["type"]
                category: str = form.cleaned_data["category"]
                amount_dollars: Decimal = form.cleaned_data["amount"]

                budget, created = Budget.objects.update_or_create(
                    user=user,
                    category=category,
                    type=type_value,
                    budget_year=year,
                    budget_month=month,
                    defaults={"amount_in_cents": int(float(amount_dollars) * 100)},
                )
                created_budgets.append(budget)

        return created_budgets

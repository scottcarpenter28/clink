from django import forms
from django.forms import formset_factory, ModelForm, BaseFormSet
from django.core.exceptions import ValidationError
from decimal import Decimal

from finance.models import Budget, BudgetAllocation, Category
from finance.utilities.budget_utils import validate_zero_based_allocation, get_expense_categories


class BudgetSetupForm(ModelForm):
    """Form for creating a budget."""

    # Override the month field with explicit configuration
    month = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }, format='%Y-%m-%d')
    )

    class Meta:
        model = Budget
        fields = ['month', 'total_income']
        widgets = {
            'total_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            })
        }

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        # Add labels
        self.fields['total_income'].label = "Total Income ($)"
        self.fields['month'].label = "Budget Month"

        # If we're editing an existing budget, make month read-only
        if self.instance and self.instance.pk:
            self.fields['month'].widget.attrs['readonly'] = True




    def save(self, commit=True):
        """Save the budget and associate it with the user."""
        budget = super().save(commit=False)
        if self.user:
            budget.user = self.user

        if commit:
            budget.save()

        return budget


class BudgetAllocationForm(forms.Form):
    """Form for a single budget allocation."""

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(category_type='expense'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    allocated_amount = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control allocation-input',
            'step': '0.01',
            'min': '0'
        })
    )

    # Read-only fields for display purposes
    spent_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-plaintext',
            'readonly': 'readonly'
        })
    )

    remaining_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-plaintext',
            'readonly': 'readonly'
        })
    )

    rollover_from_previous = forms.DecimalField(
        required=False,
        initial=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-plaintext',
            'readonly': 'readonly'
        })
    )

    # Hidden field for existing allocation UID
    allocation_uid = forms.UUIDField(required=False, widget=forms.HiddenInput())

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If user is provided, filter categories to ones they've used
        if user:
            self.fields['category'].queryset = get_expense_categories(user)


class BaseBudgetAllocationFormSet(BaseFormSet):
    """Base formset for budget allocations with zero-based validation."""

    def __init__(self, budget=None, *args, **kwargs):
        self.budget = budget
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['user'] = self.user
        return kwargs

    def clean(self):
        """Validate that allocations sum to total income."""
        if any(self.errors):
            return

        if not self.budget:
            return

        # Collect all allocation amounts
        allocations = {}
        categories = []

        for form in self.forms:
            if 'category' not in form.cleaned_data or 'allocated_amount' not in form.cleaned_data:
                continue

            category = form.cleaned_data['category']
            amount = form.cleaned_data['allocated_amount']

            # Check for duplicate categories
            if category in categories:
                raise ValidationError(f"Category '{category}' appears more than once.")

            categories.append(category)
            allocations[category.id] = Decimal(str(amount))

        # Validate zero-based budget
        if not validate_zero_based_allocation(allocations, self.budget.total_income):
            total = sum(allocations.values())
            diff = self.budget.total_income - total

            if diff > 0:
                message = f"You still have ${diff:.2f} unallocated."
            else:
                message = f"You've over-allocated by ${abs(diff):.2f}."

            raise ValidationError(message)


# Create the formset
BudgetAllocationFormSet = formset_factory(
    BudgetAllocationForm,
    formset=BaseBudgetAllocationFormSet,
    extra=0,
    can_delete=True
)


class BudgetFilterForm(forms.Form):
    """Form for filtering the budget dashboard by month."""

    year = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    month = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get years with budgets for this user
        from django.db.models import DateField
        from django.db.models.functions import ExtractYear
        from finance.models import Budget

        years = Budget.objects.filter(user=user)\
            .annotate(year=ExtractYear('month'))\
            .values_list('year', flat=True)\
            .distinct().order_by('-year')

        # Format year choices
        year_choices = [('', 'All Years')] + [(str(int(y)), str(int(y))) for y in years]
        self.fields['year'].choices = year_choices

        # Month choices
        from finance.utilities.constants import MONTH_NAMES
        month_choices = [('', 'All Months')] + [(str(k), v) for k, v in MONTH_NAMES.items()]
        self.fields['month'].choices = month_choices

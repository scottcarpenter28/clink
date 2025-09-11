from django import forms
from finance.models import Transaction, Account, Category


class TransactionForm(forms.ModelForm):
    """Base form for adding income or expense transactions"""

    def __init__(self, user, *args, transaction_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(owner=user)

        if transaction_type:
            self.fields['category'].queryset = Category.objects.filter(category_type=transaction_type)

        # Add Bootstrap CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
            })

        self.fields['account'].widget.attrs.update({
            'class': 'form-select'
        })

        self.fields['category'].widget.attrs.update({
            'class': 'form-select'
        })

        self.fields['transaction_date'].widget.attrs.update({
            'type': 'date'
        })

    class Meta:
        model = Transaction
        fields = ['account', 'category', 'vendor', 'amount', 'transaction_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': '0.00'}),
            'transaction_date': forms.DateInput(attrs={'type': 'date'}),
        }


class IncomeForm(TransactionForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, user=user, transaction_type='income', **kwargs)


class ExpenseForm(TransactionForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, user=user, transaction_type='expense', **kwargs)

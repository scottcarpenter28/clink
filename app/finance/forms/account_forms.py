from django import forms
from finance.models.account import Account
from finance.models.account_tracker import AccountTracker


class AccountForm(forms.ModelForm):
    """Form for adding new accounts"""

    class Meta:
        model = Account
        fields = ['name', 'starting_balance']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account name (e.g., "Checking Account")',
                'maxlength': 64
            }),
            'starting_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            })
        }
        labels = {
            'name': 'Account Name',
            'starting_balance': 'Starting Balance ($)'
        }
        help_texts = {
            'name': 'Give your account a descriptive name',
            'starting_balance': 'Enter the current balance of this account'
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self, commit=True):
        account = super().save(commit=False)
        account.owner = self.user
        if commit:
            account.save()
            # Create initial AccountTracker record with starting balance
            AccountTracker.objects.create(
                account=account,
                balance=account.starting_balance
            )
        return account

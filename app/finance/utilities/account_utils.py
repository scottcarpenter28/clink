from typing import List

from django.contrib.auth.models import User
from pydantic import BaseModel

from finance.models import AccountTracker, Account


def get_user_accounts(user: User):
    return user.accounts.all()


class CurrentAccountBalance(BaseModel):
    account: str
    balance: float

def get_latest_account_balance(account: Account) -> CurrentAccountBalance:
    current_balance = AccountTracker.objects.filter(account=account).order_by('-created').first()
    if current_balance:
        return CurrentAccountBalance(account=account.name, balance=current_balance.balance)
    return CurrentAccountBalance(account=account.name, balance=account.starting_balance)


def get_latest_user_account_balances(user: User) -> List[CurrentAccountBalance]:
    account_balances = []
    for account in get_user_accounts(user):
        account_balances.append(get_latest_account_balance(account))
    return account_balances

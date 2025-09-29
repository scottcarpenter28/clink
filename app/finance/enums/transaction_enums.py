from enum import Enum, auto


class TransactionType(Enum):
    INCOME = "Income"
    NEED = "Need"
    WANT = "Want"
    DEBTS = "Debts"
    SAVINGS = "Savings"
    INVESTING = "Investing"

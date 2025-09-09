from typing import Optional, Dict, Any
from django.contrib.auth.models import User
from pydantic import BaseModel

from finance.forms import IncomeForm, ExpenseForm


def get_form_class(transaction_type: str):
    return IncomeForm if transaction_type == 'income' else ExpenseForm


def format_success_message(transaction_type: str, amount: float) -> str:
    return f'{transaction_type.title()} of ${amount:.2f} added successfully!'


def get_page_title(transaction_type: str) -> str:
    return f'Add {transaction_type.title()}'


def get_submit_text(transaction_type: str) -> str:
    return f'Add {transaction_type.title()}'


class TransactionContext(BaseModel):
    form: Any
    transaction_type: str
    page_title: str
    submit_text: str
    cancel_url: str

    model_config = {
        "arbitrary_types_allowed": True
    }


class TransactionFormHandler:
    def __init__(self, user: User, transaction_type: str):
        self.user = user
        self.transaction_type = transaction_type
        self.form_class = get_form_class(transaction_type)

    def create_form(self, data: Optional[Dict] = None):
        if data:
            return self.form_class(user=self.user, data=data)
        return self.form_class(user=self.user)

    def process_form(self, form):
        if form.is_valid():
            return form.save()
        return None

    def get_context(self, form, cancel_url: str) -> TransactionContext:
        return TransactionContext(
            form=form,
            transaction_type=self.transaction_type,
            page_title=get_page_title(self.transaction_type),
            submit_text=get_submit_text(self.transaction_type),
            cancel_url=cancel_url
        )


class TransactionProcessor:
    def __init__(self, user: User, transaction_type: str):
        self.transaction_type = transaction_type
        self.form_handler = TransactionFormHandler(user, transaction_type)

    def is_valid_type(self) -> bool:
        return self.transaction_type in ['income', 'expense']

    def handle_get_request(self, cancel_url: str) -> TransactionContext:
        form = self.form_handler.create_form()
        return self.form_handler.get_context(form, cancel_url)

    def handle_post_request(self, request_data: Dict, cancel_url: str) -> tuple[Optional[Any], TransactionContext]:
        form = self.form_handler.create_form(request_data)
        transaction = self.form_handler.process_form(form)
        context = self.form_handler.get_context(form, cancel_url)
        return transaction, context

    def get_success_message(self, transaction) -> str:
        return format_success_message(self.transaction_type, transaction.amount)

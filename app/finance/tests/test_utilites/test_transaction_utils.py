from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth.models import User
from django.test import TestCase

from finance.utilities.transaction_utils import (
    get_form_class,
    format_success_message,
    get_page_title,
    get_submit_text,
    TransactionContext,
    TransactionFormHandler,
    TransactionProcessor
)
from finance.forms import IncomeForm, ExpenseForm


class TestUtilityFunctions(TestCase):

    def test_get_form_class_income(self):
        form_class = get_form_class('income')
        self.assertEqual(form_class, IncomeForm)

    def test_get_form_class_expense(self):
        form_class = get_form_class('expense')
        self.assertEqual(form_class, ExpenseForm)

    def test_get_form_class_other_type(self):
        form_class = get_form_class('other')
        self.assertEqual(form_class, ExpenseForm)

    def test_format_success_message_income(self):
        message = format_success_message('income', 100.50)
        self.assertEqual(message, 'Income of $100.50 added successfully!')

    def test_format_success_message_expense(self):
        message = format_success_message('expense', 75.25)
        self.assertEqual(message, 'Expense of $75.25 added successfully!')

    def test_format_success_message_formatting(self):
        message = format_success_message('income', 100)
        self.assertEqual(message, 'Income of $100.00 added successfully!')

    def test_get_page_title_income(self):
        title = get_page_title('income')
        self.assertEqual(title, 'Add Income')

    def test_get_page_title_expense(self):
        title = get_page_title('expense')
        self.assertEqual(title, 'Add Expense')

    def test_get_submit_text_income(self):
        text = get_submit_text('income')
        self.assertEqual(text, 'Add Income')

    def test_get_submit_text_expense(self):
        text = get_submit_text('expense')
        self.assertEqual(text, 'Add Expense')


class TestTransactionContext(TestCase):

    def setUp(self):
        self.mock_form = Mock()

    def test_transaction_context_creation(self):
        context = TransactionContext(
            form=self.mock_form,
            transaction_type='income',
            page_title='Add Income',
            submit_text='Add Income',
            cancel_url='/cancel/'
        )

        self.assertEqual(context.form, self.mock_form)
        self.assertEqual(context.transaction_type, 'income')
        self.assertEqual(context.page_title, 'Add Income')
        self.assertEqual(context.submit_text, 'Add Income')
        self.assertEqual(context.cancel_url, '/cancel/')

class TestTransactionFormHandler(TestCase):

    def setUp(self):
        self.user = Mock(spec=User)
        self.user.id = 1

    @patch('finance.utilities.transaction_utils.get_form_class')
    def test_init_income_handler(self, mock_get_form_class):
        mock_get_form_class.return_value = IncomeForm

        handler = TransactionFormHandler(self.user, 'income')

        self.assertEqual(handler.user, self.user)
        self.assertEqual(handler.transaction_type, 'income')
        self.assertEqual(handler.form_class, IncomeForm)
        mock_get_form_class.assert_called_once_with('income')

    @patch('finance.utilities.transaction_utils.get_form_class')
    def test_init_expense_handler(self, mock_get_form_class):
        mock_get_form_class.return_value = ExpenseForm

        handler = TransactionFormHandler(self.user, 'expense')

        self.assertEqual(handler.user, self.user)
        self.assertEqual(handler.transaction_type, 'expense')
        self.assertEqual(handler.form_class, ExpenseForm)
        mock_get_form_class.assert_called_once_with('expense')

    def test_create_form_without_data(self):
        with patch('finance.utilities.transaction_utils.get_form_class') as mock_get_form_class:
            mock_form_class = Mock()
            mock_form_instance = Mock()
            mock_form_class.return_value = mock_form_instance
            mock_get_form_class.return_value = mock_form_class

            handler = TransactionFormHandler(self.user, 'income')
            result = handler.create_form()

            mock_form_class.assert_called_once_with(user=self.user)
            self.assertEqual(result, mock_form_instance)

    def test_create_form_with_data(self):
        with patch('finance.utilities.transaction_utils.get_form_class') as mock_get_form_class:
            mock_form_class = Mock()
            mock_form_instance = Mock()
            mock_form_class.return_value = mock_form_instance
            mock_get_form_class.return_value = mock_form_class

            test_data = {'amount': 100.50, 'category': 1}
            handler = TransactionFormHandler(self.user, 'income')
            result = handler.create_form(test_data)

            mock_form_class.assert_called_once_with(user=self.user, data=test_data)
            self.assertEqual(result, mock_form_instance)

    def test_process_form_valid(self):
        mock_form = Mock()
        mock_form.is_valid.return_value = True
        mock_transaction = Mock()
        mock_form.save.return_value = mock_transaction

        with patch('finance.utilities.transaction_utils.get_form_class'):
            handler = TransactionFormHandler(self.user, 'income')
            result = handler.process_form(mock_form)

            mock_form.is_valid.assert_called_once()
            mock_form.save.assert_called_once()
            self.assertEqual(result, mock_transaction)

    def test_process_form_invalid(self):
        mock_form = Mock()
        mock_form.is_valid.return_value = False

        with patch('finance.utilities.transaction_utils.get_form_class'):
            handler = TransactionFormHandler(self.user, 'income')
            result = handler.process_form(mock_form)

            mock_form.is_valid.assert_called_once()
            mock_form.save.assert_not_called()
            self.assertIsNone(result)

    @patch('finance.utilities.transaction_utils.get_page_title')
    @patch('finance.utilities.transaction_utils.get_submit_text')
    def test_get_context(self, mock_get_submit_text, mock_get_page_title):
        mock_get_page_title.return_value = 'Add Income'
        mock_get_submit_text.return_value = 'Add Income'
        mock_form = Mock()
        cancel_url = '/cancel/'

        with patch('finance.utilities.transaction_utils.get_form_class'):
            handler = TransactionFormHandler(self.user, 'income')
            context = handler.get_context(mock_form, cancel_url)

            self.assertIsInstance(context, TransactionContext)
            self.assertEqual(context.form, mock_form)
            self.assertEqual(context.transaction_type, 'income')
            self.assertEqual(context.page_title, 'Add Income')
            self.assertEqual(context.submit_text, 'Add Income')
            self.assertEqual(context.cancel_url, cancel_url)

            mock_get_page_title.assert_called_once_with('income')
            mock_get_submit_text.assert_called_once_with('income')


class TestTransactionProcessor(TestCase):

    def setUp(self):
        self.user = Mock(spec=User)
        self.user.id = 1

    @patch('finance.utilities.transaction_utils.TransactionFormHandler')
    def test_init(self, mock_form_handler_class):
        mock_form_handler = Mock()
        mock_form_handler_class.return_value = mock_form_handler

        processor = TransactionProcessor(self.user, 'income')

        self.assertEqual(processor.transaction_type, 'income')
        self.assertEqual(processor.form_handler, mock_form_handler)
        mock_form_handler_class.assert_called_once_with(self.user, 'income')

    def test_is_valid_type_income(self):
        with patch('finance.utilities.transaction_utils.TransactionFormHandler'):
            processor = TransactionProcessor(self.user, 'income')
            self.assertTrue(processor.is_valid_type())

    def test_is_valid_type_expense(self):
        with patch('finance.utilities.transaction_utils.TransactionFormHandler'):
            processor = TransactionProcessor(self.user, 'expense')
            self.assertTrue(processor.is_valid_type())

    def test_is_valid_type_invalid(self):
        with patch('finance.utilities.transaction_utils.TransactionFormHandler'):
            processor = TransactionProcessor(self.user, 'invalid')
            self.assertFalse(processor.is_valid_type())

    @patch('finance.utilities.transaction_utils.TransactionFormHandler')
    def test_handle_get_request(self, mock_form_handler_class):
        mock_form_handler = Mock()
        mock_form = Mock()
        mock_context = Mock(spec=TransactionContext)

        mock_form_handler.create_form.return_value = mock_form
        mock_form_handler.get_context.return_value = mock_context
        mock_form_handler_class.return_value = mock_form_handler

        processor = TransactionProcessor(self.user, 'income')
        cancel_url = '/cancel/'
        result = processor.handle_get_request(cancel_url)

        mock_form_handler.create_form.assert_called_once_with()
        mock_form_handler.get_context.assert_called_once_with(mock_form, cancel_url)
        self.assertEqual(result, mock_context)

    @patch('finance.utilities.transaction_utils.TransactionFormHandler')
    def test_handle_post_request_valid(self, mock_form_handler_class):
        mock_form_handler = Mock()
        mock_form = Mock()
        mock_transaction = Mock()
        mock_context = Mock(spec=TransactionContext)

        mock_form_handler.create_form.return_value = mock_form
        mock_form_handler.process_form.return_value = mock_transaction
        mock_form_handler.get_context.return_value = mock_context
        mock_form_handler_class.return_value = mock_form_handler

        processor = TransactionProcessor(self.user, 'income')
        request_data = {'amount': 100.50}
        cancel_url = '/cancel/'

        transaction, context = processor.handle_post_request(request_data, cancel_url)

        mock_form_handler.create_form.assert_called_once_with(request_data)
        mock_form_handler.process_form.assert_called_once_with(mock_form)
        mock_form_handler.get_context.assert_called_once_with(mock_form, cancel_url)

        self.assertEqual(transaction, mock_transaction)
        self.assertEqual(context, mock_context)

    @patch('finance.utilities.transaction_utils.TransactionFormHandler')
    def test_handle_post_request_invalid(self, mock_form_handler_class):
        mock_form_handler = Mock()
        mock_form = Mock()
        mock_context = Mock(spec=TransactionContext)

        mock_form_handler.create_form.return_value = mock_form
        mock_form_handler.process_form.return_value = None
        mock_form_handler.get_context.return_value = mock_context
        mock_form_handler_class.return_value = mock_form_handler

        processor = TransactionProcessor(self.user, 'income')
        request_data = {'amount': 'invalid'}
        cancel_url = '/cancel/'

        transaction, context = processor.handle_post_request(request_data, cancel_url)

        self.assertIsNone(transaction)
        self.assertEqual(context, mock_context)

    @patch('finance.utilities.transaction_utils.format_success_message')
    @patch('finance.utilities.transaction_utils.TransactionFormHandler')
    def test_get_success_message(self, mock_form_handler_class, mock_format_success_message):
        mock_format_success_message.return_value = 'Income of $100.50 added successfully!'
        mock_transaction = Mock()
        mock_transaction.amount = 100.50

        processor = TransactionProcessor(self.user, 'income')
        result = processor.get_success_message(mock_transaction)

        mock_format_success_message.assert_called_once_with('income', 100.50)
        self.assertEqual(result, 'Income of $100.50 added successfully!')


class TestTransactionProcessorIntegration(TestCase):

    def setUp(self):
        self.user = Mock(spec=User)
        self.user.id = 1

    def test_integration_income_workflow(self):
        with patch('finance.utilities.transaction_utils.TransactionFormHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_form = Mock()
            mock_transaction = Mock()
            mock_transaction.amount = 150.75

            mock_handler.create_form.return_value = mock_form
            mock_handler.process_form.return_value = mock_transaction
            mock_handler.get_context.return_value = TransactionContext(
                form=mock_form,
                transaction_type='income',
                page_title='Add Income',
                submit_text='Add Income',
                cancel_url='/cancel/'
            )
            mock_handler_class.return_value = mock_handler

            processor = TransactionProcessor(self.user, 'income')

            self.assertTrue(processor.is_valid_type())

            get_context = processor.handle_get_request('/cancel/')
            self.assertEqual(get_context.transaction_type, 'income')
            self.assertEqual(get_context.page_title, 'Add Income')

            post_data = {'amount': 150.75, 'category': 1}
            transaction, post_context = processor.handle_post_request(post_data, '/cancel/')

            self.assertEqual(transaction, mock_transaction)
            self.assertEqual(post_context.transaction_type, 'income')

            success_msg = processor.get_success_message(mock_transaction)
            self.assertEqual(success_msg, 'Income of $150.75 added successfully!')

    def test_integration_expense_workflow(self):
        with patch('finance.utilities.transaction_utils.TransactionFormHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_form = Mock()
            mock_transaction = Mock()
            mock_transaction.amount = 89.99

            mock_handler.create_form.return_value = mock_form
            mock_handler.process_form.return_value = mock_transaction
            mock_handler.get_context.return_value = TransactionContext(
                form=mock_form,
                transaction_type='expense',
                page_title='Add Expense',
                submit_text='Add Expense',
                cancel_url='/cancel/'
            )
            mock_handler_class.return_value = mock_handler

            processor = TransactionProcessor(self.user, 'expense')

            self.assertTrue(processor.is_valid_type())

            success_msg = processor.get_success_message(mock_transaction)
            self.assertEqual(success_msg, 'Expense of $89.99 added successfully!')

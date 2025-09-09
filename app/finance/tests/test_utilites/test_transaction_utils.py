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
    """Test utility functions in transaction_utils"""

    def test_get_form_class_income(self):
        """Test get_form_class returns IncomeForm for income type"""
        form_class = get_form_class('income')
        self.assertEqual(form_class, IncomeForm)

    def test_get_form_class_expense(self):
        """Test get_form_class returns ExpenseForm for expense type"""
        form_class = get_form_class('expense')
        self.assertEqual(form_class, ExpenseForm)

    def test_get_form_class_other_type(self):
        """Test get_form_class returns ExpenseForm for any other type"""
        form_class = get_form_class('other')
        self.assertEqual(form_class, ExpenseForm)

    def test_format_success_message_income(self):
        """Test format_success_message for income"""
        message = format_success_message('income', 100.50)
        self.assertEqual(message, 'Income of $100.50 added successfully!')

    def test_format_success_message_expense(self):
        """Test format_success_message for expense"""
        message = format_success_message('expense', 75.25)
        self.assertEqual(message, 'Expense of $75.25 added successfully!')

    def test_format_success_message_formatting(self):
        """Test format_success_message properly formats decimals"""
        message = format_success_message('income', 100)
        self.assertEqual(message, 'Income of $100.00 added successfully!')

    def test_get_page_title_income(self):
        """Test get_page_title for income"""
        title = get_page_title('income')
        self.assertEqual(title, 'Add Income')

    def test_get_page_title_expense(self):
        """Test get_page_title for expense"""
        title = get_page_title('expense')
        self.assertEqual(title, 'Add Expense')

    def test_get_submit_text_income(self):
        """Test get_submit_text for income"""
        text = get_submit_text('income')
        self.assertEqual(text, 'Add Income')

    def test_get_submit_text_expense(self):
        """Test get_submit_text for expense"""
        text = get_submit_text('expense')
        self.assertEqual(text, 'Add Expense')


class TestTransactionContext(TestCase):
    """Test TransactionContext Pydantic model"""

    def setUp(self):
        self.mock_form = Mock()

    def test_transaction_context_creation(self):
        """Test creating a TransactionContext instance"""
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

    def test_transaction_context_arbitrary_types_allowed(self):
        """Test that arbitrary types are allowed for form field"""
        # This should not raise a validation error
        context = TransactionContext(
            form=Mock(),  # Mock is not a standard Pydantic type
            transaction_type='expense',
            page_title='Add Expense',
            submit_text='Add Expense',
            cancel_url='/cancel/'
        )
        self.assertIsNotNone(context)


class TestTransactionFormHandler(TestCase):
    """Test TransactionFormHandler class"""

    def setUp(self):
        self.user = Mock(spec=User)
        self.user.id = 1

    @patch('finance.utilities.transaction_utils.get_form_class')
    def test_init_income_handler(self, mock_get_form_class):
        """Test TransactionFormHandler initialization for income"""
        mock_get_form_class.return_value = IncomeForm

        handler = TransactionFormHandler(self.user, 'income')

        self.assertEqual(handler.user, self.user)
        self.assertEqual(handler.transaction_type, 'income')
        self.assertEqual(handler.form_class, IncomeForm)
        mock_get_form_class.assert_called_once_with('income')

    @patch('finance.utilities.transaction_utils.get_form_class')
    def test_init_expense_handler(self, mock_get_form_class):
        """Test TransactionFormHandler initialization for expense"""
        mock_get_form_class.return_value = ExpenseForm

        handler = TransactionFormHandler(self.user, 'expense')

        self.assertEqual(handler.user, self.user)
        self.assertEqual(handler.transaction_type, 'expense')
        self.assertEqual(handler.form_class, ExpenseForm)
        mock_get_form_class.assert_called_once_with('expense')

    def test_create_form_without_data(self):
        """Test create_form without data"""
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
        """Test create_form with data"""
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
        """Test process_form with valid form"""
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
        """Test process_form with invalid form"""
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
        """Test get_context method"""
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
    """Test TransactionProcessor class"""

    def setUp(self):
        self.user = Mock(spec=User)
        self.user.id = 1

    @patch('finance.utilities.transaction_utils.TransactionFormHandler')
    def test_init(self, mock_form_handler_class):
        """Test TransactionProcessor initialization"""
        mock_form_handler = Mock()
        mock_form_handler_class.return_value = mock_form_handler

        processor = TransactionProcessor(self.user, 'income')

        self.assertEqual(processor.transaction_type, 'income')
        self.assertEqual(processor.form_handler, mock_form_handler)
        mock_form_handler_class.assert_called_once_with(self.user, 'income')

    def test_is_valid_type_income(self):
        """Test is_valid_type returns True for income"""
        with patch('finance.utilities.transaction_utils.TransactionFormHandler'):
            processor = TransactionProcessor(self.user, 'income')
            self.assertTrue(processor.is_valid_type())

    def test_is_valid_type_expense(self):
        """Test is_valid_type returns True for expense"""
        with patch('finance.utilities.transaction_utils.TransactionFormHandler'):
            processor = TransactionProcessor(self.user, 'expense')
            self.assertTrue(processor.is_valid_type())

    def test_is_valid_type_invalid(self):
        """Test is_valid_type returns False for invalid type"""
        with patch('finance.utilities.transaction_utils.TransactionFormHandler'):
            processor = TransactionProcessor(self.user, 'invalid')
            self.assertFalse(processor.is_valid_type())

    @patch('finance.utilities.transaction_utils.TransactionFormHandler')
    def test_handle_get_request(self, mock_form_handler_class):
        """Test handle_get_request method"""
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
        """Test handle_post_request with valid data"""
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
        """Test handle_post_request with invalid data"""
        mock_form_handler = Mock()
        mock_form = Mock()
        mock_context = Mock(spec=TransactionContext)

        mock_form_handler.create_form.return_value = mock_form
        mock_form_handler.process_form.return_value = None  # Invalid form
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
        """Test get_success_message method"""
        mock_format_success_message.return_value = 'Income of $100.50 added successfully!'
        mock_transaction = Mock()
        mock_transaction.amount = 100.50

        processor = TransactionProcessor(self.user, 'income')
        result = processor.get_success_message(mock_transaction)

        mock_format_success_message.assert_called_once_with('income', 100.50)
        self.assertEqual(result, 'Income of $100.50 added successfully!')


class TestTransactionProcessorIntegration(TestCase):
    """Integration tests for TransactionProcessor with real utility functions"""

    def setUp(self):
        self.user = Mock(spec=User)
        self.user.id = 1

    def test_integration_income_workflow(self):
        """Test complete income workflow integration"""
        with patch('finance.utilities.transaction_utils.TransactionFormHandler') as mock_handler_class:
            # Mock the form handler and its methods
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

            # Test the processor
            processor = TransactionProcessor(self.user, 'income')

            # Test valid type check
            self.assertTrue(processor.is_valid_type())

            # Test GET request
            get_context = processor.handle_get_request('/cancel/')
            self.assertEqual(get_context.transaction_type, 'income')
            self.assertEqual(get_context.page_title, 'Add Income')

            # Test POST request
            post_data = {'amount': 150.75, 'category': 1}
            transaction, post_context = processor.handle_post_request(post_data, '/cancel/')

            self.assertEqual(transaction, mock_transaction)
            self.assertEqual(post_context.transaction_type, 'income')

            # Test success message
            success_msg = processor.get_success_message(mock_transaction)
            self.assertEqual(success_msg, 'Income of $150.75 added successfully!')

    def test_integration_expense_workflow(self):
        """Test complete expense workflow integration"""
        with patch('finance.utilities.transaction_utils.TransactionFormHandler') as mock_handler_class:
            # Mock the form handler and its methods
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

            # Test the processor
            processor = TransactionProcessor(self.user, 'expense')

            # Test valid type check
            self.assertTrue(processor.is_valid_type())

            # Test success message
            success_msg = processor.get_success_message(mock_transaction)
            self.assertEqual(success_msg, 'Expense of $89.99 added successfully!')


class TestEdgeCases(TestCase):
    """Test edge cases and boundary conditions"""

    def setUp(self):
        self.user = Mock(spec=User)
        self.user.id = 1

    def test_format_success_message_zero_amount(self):
        """Test format_success_message with zero amount"""
        message = format_success_message('income', 0.0)
        self.assertEqual(message, 'Income of $0.00 added successfully!')

    def test_format_success_message_large_amount(self):
        """Test format_success_message with large amount"""
        message = format_success_message('expense', 999999.99)
        self.assertEqual(message, 'Expense of $999999.99 added successfully!')

    def test_format_success_message_three_decimal_places(self):
        """Test format_success_message rounds to 2 decimal places"""
        message = format_success_message('income', 123.456)
        self.assertEqual(message, 'Income of $123.46 added successfully!')

    def test_get_form_class_empty_string(self):
        """Test get_form_class with empty string returns ExpenseForm"""
        form_class = get_form_class('')
        self.assertEqual(form_class, ExpenseForm)

    def test_get_form_class_none(self):
        """Test get_form_class with None returns ExpenseForm"""
        form_class = get_form_class(None)
        self.assertEqual(form_class, ExpenseForm)

    def test_get_page_title_mixed_case(self):
        """Test get_page_title properly capitalizes mixed case input"""
        title = get_page_title('InCoMe')
        self.assertEqual(title, 'Add Income')

    def test_get_submit_text_uppercase(self):
        """Test get_submit_text with uppercase input"""
        text = get_submit_text('EXPENSE')
        self.assertEqual(text, 'Add Expense')

    def test_transaction_context_with_empty_strings(self):
        """Test TransactionContext with empty string values"""
        mock_form = Mock()
        context = TransactionContext(
            form=mock_form,
            transaction_type='',
            page_title='',
            submit_text='',
            cancel_url=''
        )

        self.assertEqual(context.transaction_type, '')
        self.assertEqual(context.page_title, '')
        self.assertEqual(context.submit_text, '')
        self.assertEqual(context.cancel_url, '')

    @patch('finance.utilities.transaction_utils.get_form_class')
    def test_transaction_form_handler_create_form_empty_data(self, mock_get_form_class):
        """Test create_form with empty dict - empty dict is falsy so no data is passed"""
        mock_form_class = Mock()
        mock_form_instance = Mock()
        mock_form_class.return_value = mock_form_instance
        mock_get_form_class.return_value = mock_form_class

        handler = TransactionFormHandler(self.user, 'income')
        result = handler.create_form({})

        # Empty dict is falsy in the conditional, so no data parameter is passed
        mock_form_class.assert_called_once_with(user=self.user)
        self.assertEqual(result, mock_form_instance)

    def test_transaction_processor_is_valid_type_case_sensitivity(self):
        """Test is_valid_type is case sensitive"""
        with patch('finance.utilities.transaction_utils.TransactionFormHandler'):
            processor_upper = TransactionProcessor(self.user, 'INCOME')
            processor_mixed = TransactionProcessor(self.user, 'InCoMe')

            self.assertFalse(processor_upper.is_valid_type())
            self.assertFalse(processor_mixed.is_valid_type())

    def test_transaction_processor_is_valid_type_whitespace(self):
        """Test is_valid_type with whitespace"""
        with patch('finance.utilities.transaction_utils.TransactionFormHandler'):
            processor_space = TransactionProcessor(self.user, ' income ')
            processor_tab = TransactionProcessor(self.user, 'expense\t')

            self.assertFalse(processor_space.is_valid_type())
            self.assertFalse(processor_tab.is_valid_type())

    @patch('finance.utilities.transaction_utils.TransactionFormHandler')
    def test_handle_post_request_empty_data(self, mock_form_handler_class):
        """Test handle_post_request with empty request data"""
        mock_form_handler = Mock()
        mock_form = Mock()
        mock_context = Mock(spec=TransactionContext)

        mock_form_handler.create_form.return_value = mock_form
        mock_form_handler.process_form.return_value = None
        mock_form_handler.get_context.return_value = mock_context
        mock_form_handler_class.return_value = mock_form_handler

        processor = TransactionProcessor(self.user, 'income')
        transaction, context = processor.handle_post_request({}, '/cancel/')

        mock_form_handler.create_form.assert_called_once_with({})
        self.assertIsNone(transaction)
        self.assertEqual(context, mock_context)

    @patch('finance.utilities.transaction_utils.format_success_message')
    @patch('finance.utilities.transaction_utils.TransactionFormHandler')
    def test_get_success_message_zero_amount_transaction(self, mock_form_handler_class, mock_format_success_message):
        """Test get_success_message with zero amount transaction"""
        mock_format_success_message.return_value = 'Income of $0.00 added successfully!'
        mock_transaction = Mock()
        mock_transaction.amount = 0.0

        processor = TransactionProcessor(self.user, 'income')
        result = processor.get_success_message(mock_transaction)

        mock_format_success_message.assert_called_once_with('income', 0.0)
        self.assertEqual(result, 'Income of $0.00 added successfully!')

    def test_transaction_form_handler_process_form_exception(self):
        """Test process_form when form.save() raises exception"""
        mock_form = Mock()
        mock_form.is_valid.return_value = True
        mock_form.save.side_effect = Exception("Database error")

        with patch('finance.utilities.transaction_utils.get_form_class'):
            handler = TransactionFormHandler(self.user, 'income')

            # Should raise the exception, not catch it
            with self.assertRaises(Exception):
                handler.process_form(mock_form)

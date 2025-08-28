from django.contrib import admin
from django.utils.html import format_html
from finance.models import IncomeOrExpense


@admin.register(IncomeOrExpense)
class IncomeOrExpenseAdmin(admin.ModelAdmin):
    list_display = ('get_transaction_type', 'category', 'amount', 'account', 'created', 'updated')
    list_filter = ('category__category_type', 'category', 'account', 'created', 'updated')
    search_fields = ('category__name', 'account__name', 'account__owner__username')
    readonly_fields = ('uid', 'created', 'updated')
    ordering = ('-created',)

    fieldsets = (
        (None, {
            'fields': ('uid', 'account', 'category', 'amount')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account', 'category', 'account__owner')

    def get_transaction_type(self, obj):
        if obj.category.category_type == 'income':
            return format_html('<span style="color: green;">Income</span>')
        else:
            return format_html('<span style="color: red;">Expense</span>')

    get_transaction_type.short_description = 'Type'
    get_transaction_type.admin_order_field = 'category__category_type'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            # Order categories by type and name for better UX
            kwargs["queryset"] = db_field.related_model.objects.order_by('category_type', 'name')
        elif db_field.name == "account":
            # Only show accounts that belong to users (in case of data integrity)
            kwargs["queryset"] = db_field.related_model.objects.select_related('owner').order_by('owner__username', 'name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Custom action to calculate totals
    actions = ['calculate_selected_total']

    def calculate_selected_total(self, request, queryset):
        total_income = sum(
            transaction.amount for transaction in queryset
            if transaction.category.category_type == 'income'
        )
        total_expense = sum(
            transaction.amount for transaction in queryset
            if transaction.category.category_type == 'expense'
        )
        net_amount = total_income - total_expense

        self.message_user(
            request,
            f"Selected transactions: Income: ${total_income:.2f}, "
            f"Expenses: ${total_expense:.2f}, Net: ${net_amount:.2f}"
        )

    calculate_selected_total.short_description = "Calculate total of selected transactions"

    def save_model(self, request, obj, form, change):
        """Override to add any custom logic when saving transactions"""
        super().save_model(request, obj, form, change)
        # Here you could add logic to update AccountTracker automatically
        # when a transaction is created/modified

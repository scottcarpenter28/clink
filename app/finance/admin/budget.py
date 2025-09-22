from django.contrib import admin
from finance.models import Budget, BudgetAllocation


class BudgetAllocationInline(admin.TabularInline):
    model = BudgetAllocation
    extra = 0
    readonly_fields = ('uid', 'created', 'updated', 'spent_amount', 'remaining_amount', 'percent_spent')
    fields = ('category', 'allocated_amount', 'rollover_from_previous', 'spent_amount', 'remaining_amount', 'percent_spent')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('month_display', 'user', 'total_income', 'is_active', 'created')
    list_filter = ('is_active', 'created', 'month')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('uid', 'created', 'updated')
    ordering = ('-month',)
    inlines = [BudgetAllocationInline]

    fieldsets = (
        (None, {
            'fields': ('uid', 'user', 'month', 'total_income', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def month_display(self, obj):
        return obj.month.strftime('%B %Y')
    month_display.short_description = 'Month'
    month_display.admin_order_field = 'month'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

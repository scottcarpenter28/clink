from django.contrib import admin
from finance.models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'starting_balance', 'created', 'updated')
    list_filter = ('created', 'updated', 'owner')
    search_fields = ('name', 'owner__username', 'owner__first_name', 'owner__last_name')
    readonly_fields = ('uid', 'created', 'updated')
    ordering = ('-created',)

    fieldsets = (
        (None, {
            'fields': ('uid', 'name', 'owner', 'starting_balance')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')

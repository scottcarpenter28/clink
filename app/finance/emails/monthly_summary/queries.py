from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils import timezone


def get_users_needing_monthly_summary() -> QuerySet[User]:
    current_date = timezone.now()

    users_with_transactions_this_month = User.objects.filter(
        transaction__date_of_expense__year=current_date.year,
        transaction__date_of_expense__month=current_date.month,
    ).values_list("id", flat=True)

    return (
        User.objects.filter(
            email_settings__monthly_summary_enabled=True,
            email__isnull=False,
            id__in=users_with_transactions_this_month,
        )
        .exclude(email="")
        .distinct()
    )

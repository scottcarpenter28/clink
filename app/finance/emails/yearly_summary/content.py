from django.contrib.auth.models import User
from django.utils import timezone
from finance.emails.yearly_summary.calculations import YearlySummaryData


def build_yearly_summary_subject() -> str:
    current_date = timezone.now()
    year = current_date.year
    return f"Your {year} Year in Review"


def build_yearly_summary_content(user: User, summary_data: YearlySummaryData) -> str:
    current_date = timezone.now()
    year = current_date.year
    user_name = user.first_name or user.username

    content = f"Hello {user_name},\n\n"
    content += f"Here's your financial year in review for {year}:\n\n"

    content += "--- ANNUAL OVERVIEW ---\n"
    content += f"Total Income: ${summary_data['total_income']:.2f}\n"
    content += f"Total Expenses: ${summary_data['total_expenses']:.2f}\n"

    if summary_data["net_income"] >= 0:
        content += f"Net Income: +${summary_data['net_income']:.2f}\n\n"
    else:
        content += f"Net Income: -${abs(summary_data['net_income']):.2f}\n\n"

    if summary_data["totals_by_category"]:
        content += "--- TOP CATEGORIES ---\n"
        top_categories = summary_data["totals_by_category"][:5]
        for category_total in top_categories:
            content += f"{category_total['category']}: ${category_total['total']:.2f}\n"

        if len(summary_data["totals_by_category"]) > 5:
            content += f"\n...and {len(summary_data['totals_by_category']) - 5} more categories\n"
        content += "\n"
    else:
        content += "No transactions recorded this year.\n\n"

    content += f"Thank you for using Clink Finance throughout {year}!\n\n"
    content += "Best regards,\n"
    content += "Clink Finance Team\n\n"
    content += "---\n\n"
    content += "To manage your email preferences, log in to your account and visit your settings page.\n"

    return content

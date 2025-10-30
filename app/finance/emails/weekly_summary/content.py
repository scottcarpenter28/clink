from django.contrib.auth.models import User
from finance.emails.weekly_summary.calculations import WeeklySummaryData


def build_weekly_summary_subject() -> str:
    return "Your Weekly Spending Summary"


def build_weekly_summary_content(user: User, summary_data: WeeklySummaryData) -> str:
    user_name = user.first_name or user.username

    content = f"Hello {user_name},\n\n"
    content += "Here's a summary of your spending over the past 7 days:\n\n"

    content += "--- SPENDING BY CATEGORY ---\n"
    if summary_data["totals_by_category"]:
        for category_total in summary_data["totals_by_category"]:
            content += f"{category_total['category']}: ${category_total['total']:.2f}\n"
        content += f"\nTotal Spent: ${summary_data['grand_total']:.2f}\n\n"
    else:
        content += "No expenses recorded this week.\n\n"

    if summary_data["remaining_budgets"]:
        content += "--- BUDGET STATUS ---\n"
        for budget_info in summary_data["remaining_budgets"]:
            content += f"{budget_info['category']}: ${budget_info['spent']:.2f} / ${budget_info['budget']:.2f} "
            if budget_info["remaining"] >= 0:
                content += f"(${budget_info['remaining']:.2f} remaining)\n"
            else:
                content += f"(${abs(budget_info['remaining']):.2f} over budget)\n"
        content += "\n"

    content += "Keep up the great work tracking your finances!\n\n"
    content += "Best regards,\n"
    content += "Clink Finance Team\n\n"
    content += "---\n\n"
    content += "To manage your email preferences, log in to your account and visit your settings page.\n"

    return content

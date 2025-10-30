from django.contrib.auth.models import User
from django.utils import timezone
from finance.emails.monthly_summary.calculations import MonthlySummaryData


def build_monthly_summary_subject() -> str:
    current_date = timezone.now()
    month_name = current_date.strftime("%B")
    return f"Your {month_name} Financial Summary"


def build_monthly_summary_content(user: User, summary_data: MonthlySummaryData) -> str:
    current_date = timezone.now()
    month_name = current_date.strftime("%B")
    user_name = user.first_name or user.username

    content = f"Hello {user_name},\n\n"
    content += f"Here's your financial summary for {month_name}:\n\n"

    content += "--- INCOME & EXPENSES ---\n"
    content += f"Income: ${summary_data['income']:.2f}\n"
    content += f"Total Expenses: ${summary_data['total_expenses']:.2f}\n"

    if summary_data["income"] > 0:
        net = summary_data["income"] - summary_data["total_expenses"]
        if net >= 0:
            content += f"Net: +${net:.2f}\n\n"
        else:
            content += f"Net: -${abs(net):.2f}\n\n"
    else:
        content += "\n"

    content += "--- BREAKDOWN BY TYPE ---\n"
    if summary_data["savings"] > 0:
        content += f"Savings: ${summary_data['savings']:.2f}\n"
    if summary_data["investing"] > 0:
        content += f"Investing: ${summary_data['investing']:.2f}\n"
    if summary_data["needs"] > 0:
        content += f"Needs: ${summary_data['needs']:.2f}\n"
    if summary_data["wants"] > 0:
        content += f"Wants: ${summary_data['wants']:.2f}\n"
    if summary_data["debts"] > 0:
        content += f"Debts: ${summary_data['debts']:.2f}\n"

    if summary_data["total_expenses"] == 0:
        content += "No expenses recorded this month.\n"

    content += "\n"
    content += "Great work tracking your finances this month!\n\n"
    content += "Best regards,\n"
    content += "Clink Finance Team\n\n"
    content += "---\n\n"
    content += "To manage your email preferences, log in to your account and visit your settings page.\n"

    return content

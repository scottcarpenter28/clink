from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from finance.models import Budget, Transaction
from finance.forms import BudgetItemForm
from finance.enums.transaction_enums import TransactionType
from finance.utils.budget_calculator import (
    calculate_carry_over_for_budget,
    calculate_net_transfers_for_budget,
)


@login_required
@require_http_methods(["POST"])
def create_budget(request: HttpRequest) -> HttpResponse:
    form = BudgetItemForm(request.POST)

    if form.is_valid():
        type_name = form.cleaned_data["type"]
        category = form.cleaned_data["category"]
        amount_dollars = form.cleaned_data["amount"]
        allow_carry_over = form.cleaned_data.get("allow_carry_over", False)

        year = request.POST.get("year")
        month = request.POST.get("month")

        budget, created = Budget.objects.update_or_create(
            user=request.user,
            category=category,
            type=type_name,
            budget_year=int(year),
            budget_month=int(month),
            defaults={
                "amount_in_cents": int(float(amount_dollars) * 100),
                "allow_carry_over": allow_carry_over,
            },
        )

        return JsonResponse(
            {"success": True, "budget_id": budget.id, "created": created}
        )

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["POST"])
def update_budget(request: HttpRequest, budget_id: int) -> HttpResponse:
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    form = BudgetItemForm(request.POST)

    if form.is_valid():
        type_name = form.cleaned_data["type"]
        budget.type = type_name
        budget.category = form.cleaned_data["category"]
        amount_dollars = form.cleaned_data["amount"]
        budget.amount_in_cents = int(float(amount_dollars) * 100)
        budget.allow_carry_over = form.cleaned_data.get("allow_carry_over", False)
        budget.save()

        return JsonResponse({"success": True, "budget_id": budget.id})

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["GET"])
def get_budget(request: HttpRequest, budget_id: int) -> HttpResponse:
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    return JsonResponse(
        {
            "id": budget.id,
            "type": budget.type,
            "category": budget.category,
            "amount": float(budget.amount_dollars),
            "allow_carry_over": budget.allow_carry_over,
            "carried_over_amount": float(budget.carried_over_amount_in_cents) / 100,
        }
    )


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_budget(request: HttpRequest, budget_id: int) -> HttpResponse:
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    budget.delete()
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["GET"])
def get_budget_categories(
    request: HttpRequest, year: int, month: int, type: str
) -> HttpResponse:
    try:
        TransactionType[type]
    except KeyError:
        return JsonResponse({"success": False, "error": "Invalid type"}, status=400)

    categories = (
        Budget.objects.filter(
            user=request.user, budget_year=year, budget_month=month, type=type
        )
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    return JsonResponse({"success": True, "categories": list(categories)})


@login_required
@require_http_methods(["GET"])
def get_all_budgets(request: HttpRequest, year: int, month: int) -> HttpResponse:
    budgets = Budget.objects.filter(
        user=request.user, budget_year=year, budget_month=month
    ).order_by("category")

    budget_list = []
    for budget in budgets:
        carried_over_cents = calculate_carry_over_for_budget(
            request.user, budget.category, budget.type, year, month
        )
        net_transfer_cents = calculate_net_transfers_for_budget(budget)

        available_cents = (
            budget.amount_in_cents + carried_over_cents + net_transfer_cents
        )
        available_dollars = float(available_cents) / 100

        budget_list.append(
            {
                "id": budget.id,
                "category": budget.category,
                "type": budget.type,
                "available": f"{available_dollars:.2f}",
            }
        )

    return JsonResponse({"success": True, "budgets": budget_list})

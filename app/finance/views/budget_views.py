from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from finance.models import Budget
from finance.forms import BudgetItemForm
from finance.enums.transaction_enums import TransactionType


@login_required
@require_http_methods(["POST"])
def create_budget(request: HttpRequest) -> HttpResponse:
    form = BudgetItemForm(request.POST)

    if form.is_valid():
        type_name = form.cleaned_data["type"]
        type_value = TransactionType[type_name].value
        category = form.cleaned_data["category"]
        amount_dollars = form.cleaned_data["amount"]

        year = request.POST.get("year")
        month = request.POST.get("month")

        budget, created = Budget.objects.update_or_create(
            user=request.user,
            category=category,
            type=type_value,
            budget_year=int(year),
            budget_month=int(month),
            defaults={"amount_in_cents": int(float(amount_dollars) * 100)},
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
        budget.type = TransactionType[type_name].value
        budget.category = form.cleaned_data["category"]
        amount_dollars = form.cleaned_data["amount"]
        budget.amount_in_cents = int(float(amount_dollars) * 100)
        budget.save()

        return JsonResponse({"success": True, "budget_id": budget.id})

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_budget(request: HttpRequest, budget_id: int) -> HttpResponse:
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    budget.delete()
    return JsonResponse({"success": True})

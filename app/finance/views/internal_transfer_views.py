from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from finance.models import Budget, InternalTransfer
from finance.forms.budget_forms import InternalTransferForm


@login_required
@require_http_methods(["POST"])
def create_internal_transfer(request: HttpRequest) -> HttpResponse:
    form = InternalTransferForm(request.POST)

    if form.is_valid():
        source_budget_id = form.cleaned_data["source_budget_id"]
        destination_budget_id = form.cleaned_data.get("destination_budget_id")
        amount_dollars = form.cleaned_data["amount"]
        transfer_date = form.cleaned_data["transfer_date"]
        description = form.cleaned_data.get("description", "")

        source_budget = get_object_or_404(
            Budget, id=source_budget_id, user=request.user
        )

        destination_budget = None
        if destination_budget_id:
            destination_budget = get_object_or_404(
                Budget, id=destination_budget_id, user=request.user
            )

        transfer = InternalTransfer.objects.create(
            user=request.user,
            source_budget=source_budget,
            destination_budget=destination_budget,
            amount_in_cents=int(float(amount_dollars) * 100),
            transfer_date=transfer_date,
            description=description,
        )

        return JsonResponse(
            {
                "success": True,
                "transfer_id": transfer.id,
                "source_budget_id": source_budget.id,
                "destination_budget_id": (
                    destination_budget.id if destination_budget else None
                ),
            }
        )

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["GET"])
def get_internal_transfers(request: HttpRequest) -> HttpResponse:
    budget_id = request.GET.get("budget_id")
    year = request.GET.get("year")
    month = request.GET.get("month")

    if not budget_id and not (year and month):
        return JsonResponse(
            {
                "success": False,
                "error": "Either budget_id or year/month must be provided",
            },
            status=400,
        )

    if budget_id:
        budget = get_object_or_404(Budget, id=budget_id, user=request.user)
        transfers = InternalTransfer.objects.filter(
            user=request.user, source_budget=budget
        ) | InternalTransfer.objects.filter(
            user=request.user, destination_budget=budget
        )
    else:
        budgets = Budget.objects.filter(
            user=request.user, budget_year=int(year), budget_month=int(month)
        )
        transfers = InternalTransfer.objects.filter(
            user=request.user, source_budget__in=budgets
        ) | InternalTransfer.objects.filter(
            user=request.user, destination_budget__in=budgets
        )

    transfers = transfers.distinct().order_by("-transfer_date", "-date_created")

    transfer_list = [
        {
            "id": transfer.id,
            "source_budget_id": transfer.source_budget.id,
            "source_category": transfer.source_budget.category,
            "destination_budget_id": (
                transfer.destination_budget.id if transfer.destination_budget else None
            ),
            "destination_category": (
                transfer.destination_budget.category
                if transfer.destination_budget
                else "Used Funds"
            ),
            "amount": float(transfer.amount_dollars),
            "transfer_date": transfer.transfer_date.isoformat(),
            "description": transfer.description,
        }
        for transfer in transfers
    ]

    return JsonResponse({"success": True, "transfers": transfer_list})


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_internal_transfer(request: HttpRequest, transfer_id: int) -> HttpResponse:
    transfer = get_object_or_404(InternalTransfer, id=transfer_id, user=request.user)
    transfer.delete()
    return JsonResponse({"success": True})

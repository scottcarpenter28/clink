from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from finance.models import Transaction
from finance.forms import TransactionForm


@login_required
@require_http_methods(["POST"])
def create_transaction(request: HttpRequest) -> HttpResponse:
    form = TransactionForm(request.POST)

    if form.is_valid():
        transaction = form.save(commit=False)
        transaction.user = request.user
        transaction.save()

        return JsonResponse({"success": True, "transaction_id": transaction.id})

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["POST"])
def update_transaction(request: HttpRequest, transaction_id: int) -> HttpResponse:
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    form = TransactionForm(request.POST, instance=transaction)

    if form.is_valid():
        form.save()
        return JsonResponse({"success": True, "transaction_id": transaction.id})

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_transaction(request: HttpRequest, transaction_id: int) -> HttpResponse:
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    transaction.delete()
    return JsonResponse({"success": True})


from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.permissions import farm_worker_required

from .forms import FeedTransactionForm
from .models import FeedTransaction


@farm_worker_required
def feed_dashboard(request):

    if request.method == "POST":
        form = FeedTransactionForm(request.POST)

        if form.is_valid():

            transaction_type = form.cleaned_data[
                "transaction_type"
            ]

            quantity = form.cleaned_data["quantity"]

            if transaction_type == "USED":
                quantity = -quantity

            with transaction.atomic():

                # Check the current feed inventory.
                remaining = FeedTransaction.remaining_feed()

                if remaining + quantity < 0:
                    form.add_error(
                        "quantity",
                        "Not enough feed bags available."
                    )
                else:
                    FeedTransaction.objects.create(
                        transaction_type=transaction_type,
                        quantity=quantity,
                        business_date=timezone.localdate(),
                        recorded_by=request.user,
                        notes=form.cleaned_data["notes"]
                    )

                    messages.success(
                        request,
                        "Feed inventory updated successfully."
                    )

                    return redirect("feed_dashboard")

    else:
        form = FeedTransactionForm()

    remaining_feed = FeedTransaction.remaining_feed()

    recent_transactions = (
        FeedTransaction.objects
        .select_related("recorded_by")[:20]
    )

    return render(
        request,
        "inventory/feed_dashboard.html",
        {
            "form": form,
            "remaining_feed": remaining_feed,
            "recent_transactions": recent_transactions,
            "low_feed": remaining_feed <= 10,
        }
    )

from django.shortcuts import render

# Create your views here.
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.db.models import Sum

from inventory.models import EggStockMovement
from .models import Sale
from .forms import SaleForm
from .services import record_sale


@login_required
def sales_dashboard(request):
    form = SaleForm()

    if request.method == "POST":
        form = SaleForm(request.POST)

        if form.is_valid():
            try:
                record_sale(
                    recorded_by=request.user,
                    product_type=form.cleaned_data["product_type"],
                    quantity=form.cleaned_data["quantity"],
                    unit_price=form.cleaned_data["unit_price"],
                    trays_per_box=form.cleaned_data["trays_per_box"],
                )
                return redirect("sales_dashboard")

            except ValidationError as error:
                form.add_error(None, error)

    recent_sales = Sale.objects.order_by("-created_at")[:20]

    total_revenue = (
        Sale.objects.aggregate(total=Sum("total_amount"))["total"]
        or 0
    )

    context = {
        "form": form,
        "recent_sales": recent_sales,
        "known_eggs": EggStockMovement.current_stock(),
        "total_revenue": total_revenue,
    }

    return render(request, "sales/dashboard.html", context)

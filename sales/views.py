from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from accounts.permissions import administrator_required
from .forms import SaleCorrectionForm
from .models import SaleCorrection
from .services import correct_sale
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.shortcuts import render, redirect

from accounts.permissions import farm_worker_required
from inventory.models import EggStockMovement

from .models import Sale
from .forms import SaleForm
from .services import record_sale


@farm_worker_required
def sales_dashboard(request):

    # ==========================================
    # 1. CHECK USER ROLE
    # ==========================================

    user = request.user

    is_administrator = (
        user.is_superuser
        or user.groups.filter(
            name="Administrator"
        ).exists()
    )

    # ==========================================
    # 2. RECORD NEW SALE
    # ==========================================

    form = SaleForm()

    if request.method == "POST":

        form = SaleForm(request.POST)

        if form.is_valid():

            try:

                record_sale(
                    recorded_by=user,
                    product_type=form.cleaned_data[
                        "product_type"
                    ],
                    quantity=form.cleaned_data[
                        "quantity"
                    ],
                    unit_price=form.cleaned_data[
                        "unit_price"
                    ],
                    trays_per_box=form.cleaned_data[
                        "trays_per_box"
                    ],
                )

                return redirect("sales_dashboard")

            except ValidationError as error:

                form.add_error(None, error)

    # ==========================================
    # 3. RECENT SALES
    # ==========================================

    if is_administrator:

        recent_sales = (
            Sale.objects
            .order_by("-created_at")[:20]
        )

    else:

        # Farm Staff receive operational fields only.
        recent_sales = (
            Sale.objects
            .order_by("-created_at")
            .values(
                "business_date",
                "product_type",
                "quantity",
                "eggs_sold",
            )[:20]
        )

        # Convert each dictionary into a simple object
        # that supports the existing template fields.
        product_labels = dict(Sale.PRODUCT_CHOICES) if hasattr(
            Sale, "PRODUCT_CHOICES"
        ) else None

        staff_sales = []

        for sale in recent_sales:

            product_type = sale["product_type"]

            if product_labels is not None:
                product_label = product_labels.get(
                    product_type,
                    product_type
                )
            else:
                product_label = dict(
                    Sale._meta.get_field(
                        "product_type"
                    ).choices
                ).get(
                    product_type,
                    product_type
                )

            staff_sales.append({
                "business_date": sale["business_date"],
                "product_label": product_label,
                "quantity": sale["quantity"],
                "eggs_sold": sale["eggs_sold"],
            })

        recent_sales = staff_sales

    # ==========================================
    # 4. COMMON DASHBOARD DATA
    # ==========================================

    context = {
        "form": form,
        "recent_sales": recent_sales,
        "known_eggs": EggStockMovement.current_stock(),
        "is_administrator": is_administrator,
    }

    # ==========================================
    # 5. ADMINISTRATOR FINANCIAL DATA
    # ==========================================

    if is_administrator:

        total_revenue = (
            Sale.objects.aggregate(
                total=Sum("total_amount")
            )["total"]
            or Decimal("0.00")
        )

        context["total_revenue"] = total_revenue

    # ==========================================
    # 6. DISPLAY DASHBOARD
    # ==========================================

    return render(
        request,
        "sales/dashboard.html",
        context
    )

@administrator_required
def sales_correction_list(request):
    """
    Administrator-only sales and correction history.
    """

    sales = Sale.objects.select_related(
        "recorded_by"
    ).order_by("-business_date", "-id")[:100]

    corrections = SaleCorrection.objects.select_related(
        "sale",
        "corrected_by",
    ).order_by("-corrected_at", "-id")[:100]

    return render(
        request,
        "sales/correction_list.html",
        {
            "sales": sales,
            "corrections": corrections,
        },
    )


@administrator_required
@require_http_methods(["GET", "POST"])
def sales_correction_detail(request, sale_id):
    """
    Administrator-only correction form.
    """

    sale = get_object_or_404(Sale, pk=sale_id)

    if request.method == "POST":
        form = SaleCorrectionForm(request.POST)

        if form.is_valid():
            try:
                correct_sale(
                    sale_id=sale.id,
                    corrected_by=request.user,
                    reason=form.cleaned_data["reason"],
                    product_type=form.cleaned_data["product_type"],
                    quantity=form.cleaned_data["quantity"],
                    unit_price=form.cleaned_data["unit_price"],
                    trays_per_box=form.cleaned_data["trays_per_box"],
                )

                messages.success(
                    request,
                    f"Sale #{sale.id} corrected successfully."
                )

                return redirect("sales_correction_list")

            except ValidationError as error:
                form.add_error(None, error)

    else:
        form = SaleCorrectionForm(
            initial={
                "product_type": sale.product_type,
                "quantity": sale.quantity,
                "unit_price": sale.unit_price,
                "trays_per_box": sale.trays_per_box,
            }
        )

    return render(
        request,
        "sales/correction_detail.html",
        {
            "sale": sale,
            "form": form,
        },
    )

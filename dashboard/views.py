
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render

from accounts.permissions import farm_worker_required
from inventory.models import EggStockMovement
from production.models import Harvest
from sales.models import Sale


@farm_worker_required
def farm_overview(request):

    user = request.user

    # ==========================================
    # 1. DETERMINE USER ROLE
    # ==========================================

    is_administrator = (
        user.is_superuser
        or user.groups.filter(
            name="Administrator"
        ).exists()
    )

    # ==========================================
    # 2. EGG INVENTORY
    # ==========================================

    known_eggs = EggStockMovement.current_stock()

    full_tray_equivalent = known_eggs // 30

    # ==========================================
    # 3. PRODUCTION
    # ==========================================

    total_harvests = Harvest.objects.count()

    recent_harvests = Harvest.objects.order_by(
        "-business_date",
        "-id"
    )[:5]

    # ==========================================
    # 4. COMMON DASHBOARD INFORMATION
    # ==========================================

    context = {
        "is_administrator": is_administrator,
        "known_eggs": known_eggs,
        "full_tray_equivalent": full_tray_equivalent,
        "total_harvests": total_harvests,
        "recent_harvests": recent_harvests,
    }

    # ==========================================
    # 5. ADMINISTRATOR FINANCIAL INFORMATION
    # ==========================================

    if is_administrator:

        from accounting.models import Expense

        total_sales = Sale.objects.count()

        total_revenue = (
            Sale.objects.aggregate(
                total=Sum("total_amount")
            )["total"]
            or Decimal("0.00")
        )

        total_expenses = (
            Expense.objects.aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        net_income = total_revenue - total_expenses

        recent_sales = Sale.objects.order_by(
            "-business_date",
            "-id"
        )[:5]

        context.update({
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_income": net_income,
            "recent_sales": recent_sales,
        })

    # ==========================================
    # 6. DISPLAY DASHBOARD
    # ==========================================

    return render(
        request,
        "dashboard/overview.html",
        context
    )

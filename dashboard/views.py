
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from accounting.models import Expense
from inventory.models import EggStockMovement
from production.models import Harvest
from sales.models import Sale


@login_required
def farm_overview(request):

    # ==========================================
    # 1. CURRENT EGG INVENTORY
    # ==========================================

    known_eggs = EggStockMovement.current_stock()

    full_tray_equivalent = known_eggs // 30

    # ==========================================
    # 2. PRODUCTION SUMMARY
    # ==========================================

    total_harvests = Harvest.objects.count()

    # ==========================================
    # 3. SALES SUMMARY
    # ==========================================

    total_sales = Sale.objects.count()

    total_revenue = (
        Sale.objects.aggregate(
            total=Sum("total_amount")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # 4. EXPENSE SUMMARY
    # ==========================================

    total_expenses = (
        Expense.objects.aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # 5. NET INCOME
    # ==========================================

    net_income = total_revenue - total_expenses

    # ==========================================
    # 6. RECENT HARVESTS
    # ==========================================

    recent_harvests = Harvest.objects.order_by(
        "-business_date",
        "-id"
    )[:5]

    # ==========================================
    # 7. RECENT SALES
    # ==========================================

    recent_sales = Sale.objects.order_by(
        "-business_date",
        "-id"
    )[:5]

    # ==========================================
    # 8. DASHBOARD DATA
    # ==========================================

    context = {
        "known_eggs": known_eggs,
        "full_tray_equivalent": full_tray_equivalent,
        "total_harvests": total_harvests,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_income": net_income,
        "recent_harvests": recent_harvests,
        "recent_sales": recent_sales,
    }

    # ==========================================
    # 9. DISPLAY DASHBOARD
    # ==========================================

    return render(
        request,
        "dashboard/overview.html",
        context
    )

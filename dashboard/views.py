from django.shortcuts import render

# Create your views here.

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from inventory.models import EggStockMovement
from production.models import Harvest
from sales.models import Sale


@login_required
def farm_overview(request):

    # Current known egg inventory
    known_eggs = EggStockMovement.current_stock()

    # Total recorded harvests
    total_harvests = Harvest.objects.count()

    # Total recorded sales
    total_sales = Sale.objects.count()

    # Total sales revenue
    total_revenue = (
        Sale.objects.aggregate(
            total=Sum("total_amount")
        )["total"] or 0
    )

    # Most recent harvests and sales
    recent_harvests = Harvest.objects.order_by(
        "-business_date", "-id"
    )[:5]

    recent_sales = Sale.objects.order_by(
        "-business_date", "-id"
    )[:5]

    context = {
        "known_eggs": known_eggs,
        "full_tray_equivalent": known_eggs // 30,
        "total_harvests": total_harvests,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "recent_harvests": recent_harvests,
        "recent_sales": recent_sales,
    }

    return render(
        request,
        "dashboard/overview.html",
        context
    )

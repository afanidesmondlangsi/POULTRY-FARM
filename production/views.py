from django.shortcuts import render

# Create your views here.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from inventory.models import EggStockMovement
from inventory.models import Product, StockMovement, FeedTransaction
from .forms import HarvestForm
from .services import record_harvest
from .models import Harvest


@login_required
def production_dashboard(request):

    if request.method == "POST":
        form = HarvestForm(request.POST)

        if form.is_valid():
            record_harvest(
                worker=request.user,
                half_trays_harvested=form.cleaned_data["half_trays_harvested"],
                trays_per_box=form.cleaned_data["trays_per_box"],
                shift=form.cleaned_data["shift"],
                trays_harvested=form.cleaned_data[
                    "trays_harvested"
                ],
                boxes_harvested=form.cleaned_data[
                    "boxes_harvested"
                ]
            )

            messages.success(
                request,
                "Harvest recorded and inventory updated."
            )
        
            return redirect("production_dashboard")

    else:
        form = HarvestForm()

    tray = Product.objects.filter(
        name="Egg Tray"
    ).first()

    box = Product.objects.filter(
        name="Egg Box"
    ).first()

    tray_stock = (
        StockMovement.current_stock(tray)
        if tray else 0
    )

    box_stock = (
        StockMovement.current_stock(box)
        if box else 0
    )

    recent_harvests = Harvest.objects.select_related(
        "worker"
    ).order_by("-created_at")[:10]
    remaining_feed = FeedTransaction.remaining_feed()
        # Calculate current egg inventory
    known_eggs = EggStockMovement.current_stock()

    # Calculate packaging equivalents
    full_tray_equivalent = known_eggs // 30
    half_tray_equivalent = known_eggs // 15
    return render(
        request,
        "production/dashboard.html",
        {
            "form": form,
            "tray_stock": tray_stock,
            "box_stock": box_stock,
            "recent_harvests": recent_harvests,
            "remaining_feed": remaining_feed,
            "known_eggs": known_eggs,
            "full_tray_equivalent": full_tray_equivalent,
            "half_tray_equivalent": half_tray_equivalent,
        }
    )

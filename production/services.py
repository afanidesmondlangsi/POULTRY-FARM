
from django.db import transaction
from django.utils import timezone
from django.db import transaction
from inventory.models import EggStockMovement
from inventory.models import Product, StockMovement
from .models import Harvest


@transaction.atomic

def calculate_harvest_eggs(
    full_trays,
    half_trays,
    boxes,
    trays_per_box=None,
):
    eggs = (full_trays * 30) + (half_trays * 15)

    if boxes > 0 and trays_per_box is not None:
        eggs += boxes * trays_per_box * 30

    return eggs

def record_harvest(
    worker,
    shift,
    trays_harvested,
    boxes_harvested,
    half_trays_harvested=0,
    trays_per_box=None,
):
    today = timezone.localdate()

    tray_product = Product.objects.get(name="Egg Tray")
    box_product = Product.objects.get(name="Egg Box")

    harvest = Harvest.objects.create(
        business_date=today,
        shift=shift,
        trays_harvested=trays_harvested,
        half_trays_harvested=half_trays_harvested,
        boxes_harvested=boxes_harvested,
        trays_per_box=trays_per_box,
        worker=worker
    )

    if trays_harvested > 0:
        StockMovement.objects.create(
            product=tray_product,
            movement_type="HARVEST",
            quantity=trays_harvested,
            business_date=today,
            reference=f"HARVEST-{harvest.id}",
            created_by=worker
        )

    if boxes_harvested > 0:
        StockMovement.objects.create(
            product=box_product,
            movement_type="HARVEST",
            quantity=boxes_harvested,
            business_date=today,
            reference=f"HARVEST-{harvest.id}",
            created_by=worker
        )
    known_eggs = calculate_harvest_eggs(
        full_trays=trays_harvested,
        half_trays=half_trays_harvested,
        boxes=boxes_harvested,
        trays_per_box=trays_per_box,
    )

    if known_eggs > 0:
        EggStockMovement.objects.create(
            movement_type="HARVEST",
            eggs=known_eggs,
            business_date=harvest.business_date,
            reference=f"HARVEST-{harvest.id}",
        )
    return harvest

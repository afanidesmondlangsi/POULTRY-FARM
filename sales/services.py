
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from inventory.models import EggStockMovement
from .models import Sale


def calculate_eggs_sold(product_type, quantity, trays_per_box=None):
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero.")

    if product_type == "FULL_TRAY":
        return quantity * 30

    if product_type == "HALF_TRAY":
        return quantity * 15

    if product_type == "BOX":
        if trays_per_box is None or trays_per_box <= 0:
            raise ValidationError(
                "A valid trays-per-box value is required."
            )
        return quantity * trays_per_box * 30

    raise ValidationError("Invalid product type.")


def calculate_total_amount(quantity, unit_price):
    price = Decimal(str(unit_price))

    if quantity <= 0 or price < 0:
        raise ValidationError("Invalid quantity or selling price.")

    return quantity * price


@transaction.atomic
def record_sale(
    recorded_by,
    product_type,
    quantity,
    unit_price,
    trays_per_box=None,
):
    eggs_sold = calculate_eggs_sold(
        product_type,
        quantity,
        trays_per_box,
    )

    total_amount = calculate_total_amount(
        quantity,
        unit_price,
    )

    # Serialize sales that update the shared egg balance.
    # SQLite uses a database-level write lock.
    EggStockMovement.objects.create(
        movement_type="ADJUSTMENT",
        eggs=0,
        reference="SALE-BALANCE-CHECK",
    )

    available_eggs = (
        EggStockMovement.objects.aggregate(
            total=Sum("eggs")
        )["total"] or 0
    )

    if eggs_sold > available_eggs:
        raise ValidationError(
            f"Insufficient egg inventory. "
            f"Available: {available_eggs}; "
            f"Requested: {eggs_sold}."
        )

    sale = Sale.objects.create(
        product_type=product_type,
        quantity=quantity,
        unit_price=unit_price,
        trays_per_box=(
            trays_per_box if product_type == "BOX" else None
        ),
        total_amount=total_amount,
        eggs_sold=eggs_sold,
        recorded_by=recorded_by,
    )

    EggStockMovement.objects.create(
        movement_type="SALE",
        eggs=-eggs_sold,
        business_date=sale.business_date,
        reference=f"SALE-{sale.id}",
    )

    return sale

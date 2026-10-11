
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import SaleCorrection
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

@transaction.atomic
def correct_sale(
    *,
    sale_id,
    corrected_by,
    reason,
    product_type,
    quantity,
    unit_price,
    trays_per_box=None,
):
    """
    Correct a sale, reconcile egg inventory,
    and preserve an audit record.
    """

    # 1. Administrator authorization
    is_administrator = (
        corrected_by.is_authenticated
        and (
            corrected_by.is_superuser
            or corrected_by.groups.filter(
                name="Administrator"
            ).exists()
        )
    )

    if not is_administrator:
        raise PermissionDenied(
            "Only Administrators can correct sales."
        )

    # 2. Require a correction reason
    if not reason or not reason.strip():
        raise ValidationError(
            "A correction reason is required."
        )

    # 3. Validate corrected values
    new_eggs_sold = calculate_eggs_sold(
        product_type,
        quantity,
        trays_per_box,
    )

    new_total_amount = calculate_total_amount(
        quantity,
        unit_price,
    )

    new_trays_per_box = (
        trays_per_box if product_type == "BOX"
        else None
    )

    # 4. Load the original sale
    sale = Sale.objects.select_for_update().get(
        pk=sale_id
    )

    # 5. Calculate inventory difference
    egg_difference = (
        sale.eggs_sold - new_eggs_sold
    )

    # Serialize inventory-changing operations.
    # SQLite uses database-level write locking.
    EggStockMovement.objects.create(
        movement_type="ADJUSTMENT",
        eggs=0,
        business_date=timezone.localdate(),
        reference="SALE-CORRECTION-BALANCE-CHECK",
    )

    available_eggs = (
        EggStockMovement.current_stock()
    )

    if available_eggs + egg_difference < 0:
        raise ValidationError(
            "Correction rejected: insufficient "
            "egg inventory."
        )

    # 6. Save the original values in an audit record
    correction = SaleCorrection.objects.create(
        sale=sale,
        corrected_by=corrected_by,
        reason=reason.strip(),

        old_product_type=sale.product_type,
        old_quantity=sale.quantity,
        old_unit_price=sale.unit_price,
        old_trays_per_box=sale.trays_per_box,
        old_total_amount=sale.total_amount,
        old_eggs_sold=sale.eggs_sold,

        new_product_type=product_type,
        new_quantity=quantity,
        new_unit_price=unit_price,
        new_trays_per_box=new_trays_per_box,
        new_total_amount=new_total_amount,
        new_eggs_sold=new_eggs_sold,
    )

    # 7. Update the sale
    sale.product_type = product_type
    sale.quantity = quantity
    sale.unit_price = unit_price
    sale.trays_per_box = new_trays_per_box
    sale.total_amount = new_total_amount
    sale.eggs_sold = new_eggs_sold

    sale.save(update_fields=[
        "product_type",
        "quantity",
        "unit_price",
        "trays_per_box",
        "total_amount",
        "eggs_sold",
    ])

    # 8. Reconcile inventory
    if egg_difference != 0:
        EggStockMovement.objects.create(
            movement_type="ADJUSTMENT",
            eggs=egg_difference,
            business_date=timezone.localdate(),
            reference=f"SALE-CORRECTION-{correction.id}",
        )

    return correction

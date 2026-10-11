from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from django.utils import timezone


class Sale(models.Model):

    PRODUCT_CHOICES = [
        ("FULL_TRAY", "Full Tray"),
        ("HALF_TRAY", "Half Tray"),
        ("BOX", "Box"),
    ]

    business_date = models.DateField(
        default=timezone.localdate
    )

    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_CHOICES
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    # Required for box sales; blank for trays
    trays_per_box = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    eggs_sold = models.PositiveIntegerField()

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.get_product_type_display()} "
            f"x {self.quantity} - {self.total_amount}"
        )

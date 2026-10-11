from django.db import models

# Create your models here.
from django.utils import timezone
from django.conf import settings
from django.db import models


class Product(models.Model):
    UNIT_CHOICES = [
        ("TRAY", "Tray"),
        ("BOX", "Box"),
        ("EGG", "Individual Egg"),
    ]

    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    MOVEMENT_CHOICES = [
        ("HARVEST", "Harvest"),
        ("SALE", "Sale"),
        ("DAMAGE", "Damage"),
        ("PURCHASE", "Purchase"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_movements"
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_CHOICES
    )

    # Positive for stock received, negative for stock removed
    quantity = models.IntegerField()

    business_date = models.DateField()

    reference = models.CharField(
        max_length=100,
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name}: {self.quantity}"

    @classmethod
    def current_stock(cls, product):
        from django.db.models import Sum

        result = cls.objects.filter(
            product=product
        ).aggregate(total=Sum("quantity"))

        return result["total"] or 0

class FeedTransaction(models.Model):

    TRANSACTION_TYPES = [
        ("RECEIVED", "Feed Received"),
        ("USED", "Feed Used"),
        ("ADJUSTMENT", "Stock Adjustment"),
    ]

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )

    # Positive for received feed, negative for used feed
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    business_date = models.DateField()

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    created_at = models.DateTimeField(auto_now_add=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transaction_type}: {self.quantity} bags"

    @classmethod
    def remaining_feed(cls):
        from django.db.models import Sum

        result = cls.objects.aggregate(
            total=Sum("quantity")
        )

        return result["total"] or 0

class EggStockMovement(models.Model):
    MOVEMENT_CHOICES = [
        ("HARVEST", "Harvest"),
        ("SALE", "Sale"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_CHOICES
    )

    # Positive for additions, negative for deductions
    eggs = models.IntegerField()

    business_date = models.DateField(
        default=timezone.localdate
    )

    reference = models.CharField(
        max_length=100,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @classmethod
    def current_stock(cls):
        from django.db.models import Sum

        return (
            cls.objects.aggregate(total=Sum("eggs"))["total"]
            or 0
        )

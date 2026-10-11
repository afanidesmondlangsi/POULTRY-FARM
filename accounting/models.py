from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class Expense(models.Model):

    CATEGORY_CHOICES = [
        ("FEED", "Feed Purchase"),
        ("TRANSPORT", "Transportation"),
        ("SALARY", "Employee Salary"),
        ("UTILITIES", "Utilities"),
        ("MEDICATION", "Medication and Veterinary"),
        ("MAINTENANCE", "Maintenance"),
        ("OTHER", "Other Expense"),
    ]

    business_date = models.DateField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    description = models.CharField(
        max_length=255
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"))
        ]
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-business_date", "-created_at"]

    def __str__(self):
        return (
            f"{self.business_date} - "
            f"{self.get_category_display()} - "
            f"{self.amount}"
        )

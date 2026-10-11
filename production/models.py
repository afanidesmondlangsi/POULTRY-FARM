from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models
from django.utils import timezone



class Harvest(models.Model):
    SHIFT_CHOICES = [
        ("MORNING", "Morning"),
        ("AFTERNOON", "Afternoon"),
        ("EVENING", "Evening"),
    ]

    business_date = models.DateField(
        default=timezone.localdate
    )

    shift = models.CharField(
        max_length=20,
        choices=SHIFT_CHOICES
    )

    trays_harvested = models.PositiveIntegerField(default=0)

    half_trays_harvested = models.PositiveIntegerField(default=0)

    boxes_harvested = models.PositiveIntegerField(default=0)

    trays_per_box = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional: number of full trays in each box"
    )

    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Harvest {self.business_date} "
            f"({self.shift})"
        )

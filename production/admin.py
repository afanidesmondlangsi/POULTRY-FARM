from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Harvest


@admin.register(Harvest)
class HarvestAdmin(admin.ModelAdmin):
    list_display = (
        "business_date",
        "shift",
        "trays_harvested",
        "boxes_harvested",
        "worker"
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

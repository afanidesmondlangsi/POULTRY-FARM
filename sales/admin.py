from django.contrib import admin

# Register your models here.

from django.contrib import admin

from .models import Sale, SaleCorrection


class ReadOnlySalesAdmin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Sale)
class SaleAdmin(ReadOnlySalesAdmin, admin.ModelAdmin):

    list_display = (
        "id",
        "business_date",
        "product_type",
        "quantity",
        "unit_price",
        "total_amount",
        "recorded_by",
        "created_at",
    )

    list_filter = (
        "business_date",
        "product_type",
    )

    search_fields = (
        "id",
        "recorded_by__username",
    )

    def has_view_permission(self, request, obj=None):
        return (
            request.user.is_superuser
            or request.user.groups.filter(
                name="Administrator"
            ).exists()
        )


@admin.register(SaleCorrection)
class SaleCorrectionAdmin(
    ReadOnlySalesAdmin,
    admin.ModelAdmin
):

    list_display = (
        "id",
        "sale",
        "corrected_by",
        "reason",
        "corrected_at",
    )

    readonly_fields = (
        "sale",
        "corrected_by",
        "reason",
        "old_product_type",
        "old_quantity",
        "old_unit_price",
        "old_trays_per_box",
        "old_total_amount",
        "old_eggs_sold",
        "new_product_type",
        "new_quantity",
        "new_unit_price",
        "new_trays_per_box",
        "new_total_amount",
        "new_eggs_sold",
        "corrected_at",
    )

    def has_view_permission(self, request, obj=None):
        return (
            request.user.is_superuser
            or request.user.groups.filter(
                name="Administrator"
            ).exists()
        )

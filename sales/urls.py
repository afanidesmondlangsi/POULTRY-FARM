
from django.urls import path

from .views import (
    sales_dashboard,
    sales_correction_list,
    sales_correction_detail,
)

urlpatterns = [
    path(
        "",
        sales_dashboard,
        name="sales_dashboard",
    ),
    path(
        "corrections/",
        sales_correction_list,
        name="sales_correction_list",
    ),
    path(
        "corrections/<int:sale_id>/",
        sales_correction_detail,
        name="sales_correction_detail",
    ),
]

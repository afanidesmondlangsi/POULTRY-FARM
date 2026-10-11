
from django.contrib import admin
from django.urls import path, include

urlpatterns = [

    # Main Farm Overview homepage
    path(
        "",
        include("dashboard.urls")
    ),

    # Django Administration
    path(
        "admin/",
        admin.site.urls
    ),

    # Production Management
    path(
        "production/",
        include("production.urls")
    ),

    # Inventory Management
    path(
        "inventory/",
        include("inventory.urls")
    ),

    # Sales Management
    path(
        "sales/",
        include("sales.urls")
    ),
path("accounting/", include("accounting.urls")),
]


from django.urls import path

from .views import accounting_dashboard


urlpatterns = [
    path(
        "",
        accounting_dashboard,
        name="accounting_dashboard"
    ),
]

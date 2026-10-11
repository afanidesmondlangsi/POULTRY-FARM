
from django.urls import path
from .views import production_dashboard

urlpatterns = [
    path(
        "",
        production_dashboard,
        name="production_dashboard"
    ),
]

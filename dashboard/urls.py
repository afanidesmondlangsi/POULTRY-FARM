
from django.urls import path
from .views import farm_overview

urlpatterns = [
    path("", farm_overview, name="farm_overview"),
]

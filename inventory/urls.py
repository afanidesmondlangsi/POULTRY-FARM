
from django.urls import path
from .views import feed_dashboard

urlpatterns = [
    path(
        "feed/",
        feed_dashboard,
        name="feed_dashboard"
    ),
]

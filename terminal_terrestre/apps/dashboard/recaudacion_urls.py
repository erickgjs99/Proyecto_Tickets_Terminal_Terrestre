"""apps/dashboard/recaudacion_urls.py"""
from django.urls import path
from .recaudacion_views import RecaudacionesView

urlpatterns = [
    path("", RecaudacionesView.as_view(), name="recaudaciones"),
]

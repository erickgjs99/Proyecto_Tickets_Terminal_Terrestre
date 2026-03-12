"""apps/qr_codes/urls.py"""
from django.urls import path
from .views import GenerarTicketView, HikvisionConfigView, HikvisionTestView

urlpatterns = [
    path("generar/",     GenerarTicketView.as_view(),  name="qr_generar"),
    path("config/",      HikvisionConfigView.as_view(), name="hikvision_config"),
    path("config/test/", HikvisionTestView.as_view(),   name="hikvision_test"),
]

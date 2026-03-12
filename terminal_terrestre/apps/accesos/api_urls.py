"""apps/accesos/api_urls.py"""
from django.urls import path
from .views import ValidarQRAPIView

urlpatterns = [
    path("validar/", ValidarQRAPIView.as_view(), name="api_validar_qr"),
]

"""
apps/accesos/models.py
=======================
Registro de validaciones de QR en el torniquete o lectores externos.
"""

from django.db import models

from apps.qr_codes.models import TicketQR


class ResultadoAcceso(models.TextChoices):
    PERMITIDO = "permitido", "Permitido"
    DENEGADO = "denegado", "Denegado"


class Acceso(models.Model):
    """
    Log de cada intento de acceso con QR.
    El campo qr_code es nullable: puede haber intentos con códigos inválidos.
    """

    qr_contenido = models.CharField(max_length=100, verbose_name="Contenido del QR")
    qr_code = models.ForeignKey(
        TicketQR,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accesos",
        verbose_name="Ticket QR",
    )
    resultado = models.CharField(
        max_length=10,
        choices=ResultadoAcceso.choices,
        verbose_name="Resultado",
    )
    razon = models.CharField(max_length=200, blank=True, verbose_name="Razón")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Acceso"
        verbose_name_plural = "Accesos"
        ordering = ["-fecha"]
        indexes = [models.Index(fields=["fecha", "resultado"])]

    def __str__(self) -> str:
        return f"[{self.fecha:%Y-%m-%d %H:%M}] {self.qr_contenido} → {self.resultado}"

"""
apps/tickets/models.py
=======================
Tipos de ticket del Terminal Terrestre con precio y estado.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class TipoTicket(models.Model):
    """
    Tipo de ticket con precio.
    Corresponde al tarifario oficial del terminal de Cariamanga.
    El administrador puede crear tipos adicionales dinámicamente.
    """

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre",
    )
    prefijo = models.CharField(
        max_length=10,
        default="TK",
        verbose_name="Prefijo de numeración",
        help_text="Siglas del número de ticket. Ej: BIP → BIP-000001",
    )
    precio = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Precio (USD)",
    )
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Ticket"
        verbose_name_plural = "Tipos de Ticket"
        ordering = ["nombre"]
        indexes = [models.Index(fields=["activo"])]

    def __str__(self) -> str:
        return f"{self.nombre} (${self.precio})"

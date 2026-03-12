"""
apps/cooperativas/models.py
============================
Modelo de cooperativas de transporte del terminal.
"""

from django.db import models


class EstadoCooperativa(models.TextChoices):
    ACTIVO = "activo", "Activo"
    INACTIVO = "inactivo", "Inactivo"
    AGOTADO = "agotado", "Agotado"


class Cooperativa(models.Model):
    """
    Cooperativa o empresa de transporte que opera en el terminal.
    Mantiene un contador de boletos disponibles vs utilizados.
    """

    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nombre",
    )
    max_boletos = models.PositiveIntegerField(
        default=0,
        verbose_name="Máximo de boletos",
        help_text="0 = sin límite",
    )
    boletos_utilizados = models.PositiveIntegerField(
        default=0,
        verbose_name="Boletos utilizados",
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoCooperativa.choices,
        default=EstadoCooperativa.ACTIVO,
        verbose_name="Estado",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cooperativa"
        verbose_name_plural = "Cooperativas"
        ordering = ["nombre"]
        indexes = [models.Index(fields=["estado"])]

    def __str__(self) -> str:
        return self.nombre

    @property
    def tiene_boletos_disponibles(self) -> bool:
        if self.max_boletos == 0:
            return True
        return self.boletos_utilizados < self.max_boletos

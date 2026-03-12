"""
apps/ventas/models.py
======================
Modelo de ventas con numeración secuencial de tickets (TK-000001).
El número de ticket es continuo y se pasa entre operadores al cambiar turno.
"""

from django.db import models, transaction

from apps.cooperativas.models import Cooperativa
from apps.qr_codes.models import TicketQR
from apps.tickets.models import TipoTicket
from apps.usuarios.models import Usuario


class Venta(models.Model):
    """
    Registro de cada transacción de venta.
    El número de ticket (TK-000001) se genera automáticamente y es secuencial,
    continuando entre operadores sin reinicio al cambiar de turno.
    """

    numero_ticket = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="Número de ticket",
        help_text="Formato: TK-000001. Secuencial por tipo de ticket.",
    )
    ticket_qr = models.OneToOneField(
        TicketQR,
        on_delete=models.PROTECT,
        related_name="venta",
        verbose_name="Ticket QR",
    )
    tipo_ticket = models.ForeignKey(
        TipoTicket,
        on_delete=models.PROTECT,
        related_name="ventas",
        verbose_name="Tipo de ticket",
    )
    precio = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Precio",
    )
    cooperativa = models.ForeignKey(
        Cooperativa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
        verbose_name="Cooperativa",
    )
    operador = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ventas",
        verbose_name="Operador",
    )
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha"]
        unique_together = [("tipo_ticket", "numero_ticket")]
        indexes = [
            models.Index(fields=["operador", "fecha"]),
            models.Index(fields=["tipo_ticket", "fecha"]),
            models.Index(fields=["cooperativa", "fecha"]),
        ]

    def __str__(self) -> str:
        return f"{self.numero_ticket} — {self.tipo_ticket.nombre} ${self.precio}"

    def save(self, *args, **kwargs):
        """Asigna número de ticket secuencial por tipo antes del primer guardado."""
        if not self.numero_ticket:
            with transaction.atomic():
                self.numero_ticket = self._siguiente_numero_ticket(self.tipo_ticket)
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    @classmethod
    def _siguiente_numero_ticket(cls, tipo_ticket) -> str:
        """
        Calcula el siguiente número secuencial en formato {PREFIJO}-XXXXXX
        dentro del mismo tipo de ticket, usando el prefijo configurado en TipoTicket.
        Ej: BIP-000001, TK-000001, etc.
        """
        prefijo = (getattr(tipo_ticket, "prefijo", None) or "TK").strip().upper()
        ultimo = (
            cls.objects
            .select_for_update()
            .filter(tipo_ticket=tipo_ticket)
            .order_by("-id")
            .first()
        )
        if ultimo:
            try:
                # El número está siempre después del primer guion
                numero_actual = int(ultimo.numero_ticket.split("-", 1)[1])
                siguiente = numero_actual + 1
            except (ValueError, IndexError):
                siguiente = 1
        else:
            siguiente = 1
        return f"{prefijo}-{siguiente:06d}"

"""
apps/qr_codes/models.py
========================
Modelos principales del sistema:
  - ConfiguracionHikvision: parámetros de conexión al dispositivo (singleton)
  - TicketQR: registro de cada QR generado y enviado al torniquete
"""

from django.db import models

from apps.cooperativas.models import Cooperativa
from apps.tickets.models import TipoTicket
from apps.usuarios.models import Usuario


class ConfiguracionHikvision(models.Model):
    """
    Configuración de conexión al dispositivo Hikvision.
    Patrón Singleton: solo debe existir un registro activo.
    Editable desde el panel de administración o el endpoint de config.
    """

    nombre = models.CharField(
        max_length=100,
        default="Torniquete Principal",
        verbose_name="Nombre del dispositivo",
    )
    ip = models.CharField(max_length=50, verbose_name="Dirección IP")
    puerto = models.PositiveIntegerField(default=80, verbose_name="Puerto")
    protocolo = models.CharField(
        max_length=10,
        default="http",
        choices=[("http", "HTTP"), ("https", "HTTPS")],
        verbose_name="Protocolo",
    )
    usuario = models.CharField(max_length=50, default="admin", verbose_name="Usuario")
    password = models.CharField(max_length=100, verbose_name="Contraseña")
    puerta = models.PositiveIntegerField(default=1, verbose_name="Número de puerta")
    minutos_expiracion_default = models.PositiveIntegerField(
        default=10,
        verbose_name="Minutos de expiración por defecto",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración Hikvision"
        verbose_name_plural = "Configuración Hikvision"

    def __str__(self) -> str:
        return f"{self.nombre} ({self.protocolo}://{self.ip}:{self.puerto})"

    @property
    def url_base(self) -> str:
        """URL base del dispositivo sin trailing slash."""
        return f"{self.protocolo}://{self.ip}:{self.puerto}"


class EstadoTicket(models.TextChoices):
    ACTIVO = "activo", "Activo"
    USADO = "usado", "Usado"
    EXPIRADO = "expirado", "Expirado"
    ERROR = "error", "Error"


class TicketQR(models.Model):
    """
    Registro de cada QR generado en el sistema.

    El campo `codigo` es el employeeNo/cardNo enviado a Hikvision.
    La imagen QR en base64 se almacena directamente en BD para facilitar
    la impresión sin necesidad de archivos externos.

    El número de ticket secuencial (TK-000001) se asigna automáticamente
    en el modelo Venta al momento de crear la transacción.
    """

    codigo = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Código único",
        help_text="employeeNo y cardNo enviado a Hikvision",
    )
    tipo_ticket = models.ForeignKey(
        TipoTicket,
        on_delete=models.PROTECT,
        related_name="tickets_qr",
        verbose_name="Tipo de ticket",
    )
    precio = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Precio cobrado",
    )
    cooperativa = models.ForeignKey(
        Cooperativa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_qr",
        verbose_name="Cooperativa",
    )
    minutos_expiracion = models.PositiveIntegerField(
        verbose_name="Minutos de expiración",
    )
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de inicio")
    fecha_expiracion = models.DateTimeField(
        db_index=True,
        verbose_name="Fecha de expiración",
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoTicket.choices,
        default=EstadoTicket.ACTIVO,
        db_index=True,
        verbose_name="Estado",
    )
    imagen_qr_base64 = models.TextField(
        verbose_name="Imagen QR (base64)",
        help_text="data:image/png;base64,...",
    )

    # Estado de integración con Hikvision
    hik_usuario_ok = models.BooleanField(
        default=False,
        verbose_name="Usuario Hikvision creado",
    )
    hik_tarjeta_ok = models.BooleanField(
        default=False,
        verbose_name="Tarjeta QR asignada en Hikvision",
    )
    hik_respuesta = models.TextField(
        blank=True,
        verbose_name="Respuesta Hikvision (raw)",
    )

    operador = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="tickets_generados",
        verbose_name="Operador",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    fecha_uso = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de uso",
    )

    class Meta:
        verbose_name = "Ticket QR"
        verbose_name_plural = "Tickets QR"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["estado", "fecha_expiracion"]),
            models.Index(fields=["operador", "fecha_creacion"]),
        ]

    def __str__(self) -> str:
        return f"QR {self.codigo} — {self.tipo_ticket.nombre} [{self.estado}]"

    @property
    def hik_integracion_ok(self) -> bool:
        """True si ambas operaciones Hikvision fueron exitosas."""
        return self.hik_usuario_ok and self.hik_tarjeta_ok

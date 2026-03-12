"""
apps/usuarios/models.py
=======================
Modelo de usuario extendido con roles y sistema de auditoría.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class RolUsuario(models.TextChoices):
    ADMIN = "admin", "Administrador"
    OPERADOR = "operador", "Operador"
    SUPERVISOR = "supervisor", "Supervisor"


class Usuario(AbstractUser):
    """
    Usuario del sistema con rol asignado.
    Extiende AbstractUser para mantener compatibilidad con Django admin.
    """

    rol = models.CharField(
        max_length=20,
        choices=RolUsuario.choices,
        default=RolUsuario.OPERADOR,
        verbose_name="Rol",
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Teléfono",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    cooperativa = models.ForeignKey(
        "cooperativas.Cooperativa",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="Cooperativa asignada",
    )
    tipos_ticket_permitidos = models.ManyToManyField(
        "tickets.TipoTicket",
        blank=True,
        related_name="operadores_permitidos",
        verbose_name="Tipos de ticket permitidos",
        help_text="Tipos de ticket que este usuario puede generar. Vacío = todos (solo admin/supervisor).",
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["username"]

    def __str__(self) -> str:
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    @property
    def es_admin(self) -> bool:
        return self.rol == RolUsuario.ADMIN

    @property
    def es_operador(self) -> bool:
        return self.rol == RolUsuario.OPERADOR

    @property
    def es_supervisor(self) -> bool:
        return self.rol == RolUsuario.SUPERVISOR


class LogAuditoria(models.Model):
    """
    Registro de auditoría de todas las acciones críticas del sistema.
    """

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="logs_auditoria",
        verbose_name="Usuario",
    )
    accion = models.CharField(max_length=100, verbose_name="Acción")
    modelo = models.CharField(max_length=100, verbose_name="Modelo afectado")
    detalle = models.TextField(blank=True, verbose_name="Detalle")
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="Dirección IP"
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["usuario", "fecha"]),
            models.Index(fields=["modelo", "fecha"]),
        ]

    def __str__(self) -> str:
        return f"[{self.fecha:%Y-%m-%d %H:%M}] {self.usuario} → {self.accion}"

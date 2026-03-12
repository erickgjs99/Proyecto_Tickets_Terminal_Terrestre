"""
apps/usuarios/admin.py
=======================
Registro de modelos en el panel de administración Django.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import LogAuditoria, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", "email", "rol", "cooperativa", "activo"]
    list_filter = ["rol", "activo", "is_staff", "cooperativa"]
    search_fields = ["username", "first_name", "last_name", "email"]
    filter_horizontal = ("tipos_ticket_permitidos",)
    fieldsets = UserAdmin.fieldsets + (
        (
            "Información adicional",
            {
                "fields": (
                    "rol",
                    "telefono",
                    "activo",
                    "cooperativa",
                    "tipos_ticket_permitidos",
                )
            },
        ),
    )


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ["fecha", "usuario", "accion", "modelo", "ip_address"]
    list_filter = ["accion", "modelo"]
    search_fields = ["usuario__username", "accion", "detalle"]
    readonly_fields = ["fecha", "usuario", "accion", "modelo", "detalle", "ip_address"]

    def has_add_permission(self, request):
        return False  # Los logs solo se crean automáticamente

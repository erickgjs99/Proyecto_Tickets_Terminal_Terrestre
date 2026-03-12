"""
apps/usuarios/permissions.py
=============================
Clases de permisos personalizadas para DRF basadas en roles de usuario.
"""

from rest_framework.permissions import BasePermission

from .models import RolUsuario


class EsAdmin(BasePermission):
    """Permite acceso únicamente a usuarios con rol Administrador."""

    message = "Solo los administradores pueden realizar esta acción."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol == RolUsuario.ADMIN
        )


class EsAdminOSupervisor(BasePermission):
    """Permite acceso a Administradores y Supervisores."""

    message = "Se requiere rol de Administrador o Supervisor."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in (RolUsuario.ADMIN, RolUsuario.SUPERVISOR)
        )


class EsAdminOReadOnly(BasePermission):
    """
    Permite lectura a cualquier usuario autenticado.
    Escritura (POST, PUT, PATCH, DELETE) solo a Administradores.
    """

    message = "Se requiere rol de Administrador para modificar recursos."

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.rol == RolUsuario.ADMIN

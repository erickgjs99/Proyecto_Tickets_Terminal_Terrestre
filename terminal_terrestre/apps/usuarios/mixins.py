"""
apps/usuarios/mixins.py
========================
Mixins reutilizables para vistas basadas en clases.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import RolUsuario


class RolRequeridoMixin(LoginRequiredMixin):
    """
    Requiere que el usuario tenga uno de los roles especificados.
    Uso: roles_permitidos = [RolUsuario.ADMIN, RolUsuario.SUPERVISOR]
    """

    roles_permitidos: list = []

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response
        if self.roles_permitidos and request.user.rol not in self.roles_permitidos:
            raise PermissionDenied("No tienes permisos para acceder a esta sección.")
        return response


class SoloAdminMixin(RolRequeridoMixin):
    roles_permitidos = [RolUsuario.ADMIN]


class AdminOSupervisorMixin(RolRequeridoMixin):
    roles_permitidos = [RolUsuario.ADMIN, RolUsuario.SUPERVISOR]

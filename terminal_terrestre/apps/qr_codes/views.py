"""
apps/qr_codes/views.py
=======================
Vistas Django (HTML templates) para el módulo QR.
"""

import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from apps.cooperativas.models import Cooperativa
from apps.tickets.models import TipoTicket
from apps.usuarios.mixins import SoloAdminMixin
from apps.ventas.models import Venta

from .models import ConfiguracionHikvision, EstadoTicket, TicketQR
from .services import HikvisionService, generar_qr_base64

logger = logging.getLogger(__name__)

MINUTOS_OPCIONES = [5, 10, 15, 20, 30, 60]


def _generar_codigo_unico() -> str:
    """
    Genera el employee_no igual que el script original:
      str(int(time.time())) → 10 dígitos numéricos (timestamp Unix)
    Ejemplo: "1717200000"
    """
    import time
    return str(int(time.time()))


class GenerarTicketView(LoginRequiredMixin, View):
    """
    GET  /qr/generar/ — Formulario de generación
    POST /qr/generar/ — Genera el ticket QR completo
    """

    template_name = "qr_codes/generar.html"

    def _tipos_permitidos(self, user):
        """Devuelve los TipoTicket activos que el usuario puede generar."""
        if user.es_admin or user.es_supervisor:
            return TipoTicket.objects.filter(activo=True)
        permitidos = user.tipos_ticket_permitidos.filter(activo=True)
        return permitidos

    def _ctx(self, request, form_data=None):
        return {
            "tipos_ticket": self._tipos_permitidos(request.user),
            "minutos_opciones": MINUTOS_OPCIONES,
            "minutos_default": 10,
            "tickets_recientes": TicketQR.objects.select_related(
                "tipo_ticket", "cooperativa", "venta"
            ).order_by("-fecha_creacion")[:12],
            "form_data": form_data or {},
        }

    def get(self, request):
        return render(request, self.template_name, self._ctx(request))

    def post(self, request):
        tipo_id     = request.POST.get("tipo_ticket")
        minutos_raw = request.POST.get("minutos_expiracion", "").strip()
        form_data   = {"tipo_ticket": tipo_id, "minutos_expiracion": minutos_raw}

        try:
            tipo = self._tipos_permitidos(request.user).get(id=tipo_id)
        except TipoTicket.DoesNotExist:
            messages.error(request, "Tipo de ticket inválido, inactivo o no permitido.")
            return render(request, self.template_name, self._ctx(request, form_data))

        # Cooperativa se toma automáticamente del usuario autenticado
        cooperativa = getattr(request.user, "cooperativa", None)

        config = ConfiguracionHikvision.objects.filter(activo=True).first()
        if not config:
            messages.error(request, "No hay configuración Hikvision activa. Contacte al administrador.")
            return render(request, self.template_name, self._ctx(request, form_data))

        try:
            minutos = int(minutos_raw) if minutos_raw else config.minutos_expiracion_default
            if not (1 <= minutos <= 1440):
                raise ValueError
        except ValueError:
            messages.error(request, "Tiempo de expiración inválido (1–1440 minutos).")
            return render(request, self.template_name, self._ctx(request, form_data))

        codigo = _generar_codigo_unico()
        ahora  = timezone.now()
        expira = ahora + timedelta(minutes=minutos)

        hik_service = HikvisionService(config)
        res_usuario, res_tarjeta = hik_service.crear_pase_completo(
            employee_no=codigo, inicio=ahora, fin=expira
        )

        if not (res_usuario.exitoso and res_tarjeta.exitoso):
            logger.warning(
                "Hikvision falló — usuario_ok=%s tarjeta_ok=%s | %s",
                res_usuario.exitoso, res_tarjeta.exitoso,
                f"Usuario: {res_usuario.respuesta_raw[:200]} | Tarjeta: {res_tarjeta.respuesta_raw[:200]}",
            )
            messages.error(
                request,
                "No se pudo registrar el acceso en el dispositivo Hikvision. "
                "El ticket no fue generado. Verifique la conexión con el dispositivo.",
            )
            return render(request, self.template_name, self._ctx(request, form_data))

        respuesta_hik = (
            f"Usuario: {res_usuario.respuesta_raw[:300]} | Tarjeta: {res_tarjeta.respuesta_raw[:300]}"
        )

        imagen_qr = generar_qr_base64(codigo)

        ticket = TicketQR.objects.create(
            codigo=codigo, tipo_ticket=tipo, precio=tipo.precio,
            cooperativa=cooperativa, minutos_expiracion=minutos,
            fecha_inicio=ahora, fecha_expiracion=expira, estado=EstadoTicket.ACTIVO,
            imagen_qr_base64=imagen_qr,
            hik_usuario_ok=True, hik_tarjeta_ok=True,
            hik_respuesta=respuesta_hik, operador=request.user,
        )

        Venta.objects.create(
            ticket_qr=ticket, tipo_ticket=tipo, precio=tipo.precio,
            cooperativa=cooperativa, operador=request.user,
        )

        if cooperativa:
            cooperativa.boletos_utilizados += 1
            cooperativa.save(update_fields=["boletos_utilizados"])

        ctx = self._ctx(request, form_data)
        ctx["ticket"] = TicketQR.objects.select_related(
            "tipo_ticket", "cooperativa", "venta"
        ).get(pk=ticket.pk)
        return render(request, self.template_name, ctx)


class HikvisionConfigView(SoloAdminMixin, View):
    """GET/POST /qr/config/ — Configuración del dispositivo."""

    template_name = "qr_codes/hikvision_config.html"

    def _get_config(self):
        config, _ = ConfiguracionHikvision.objects.get_or_create(
            activo=True,
            defaults={"ip": "172.168.109.5", "puerto": 80, "usuario": "admin", "password": "admin", "puerta": 1},
        )
        return config

    def get(self, request):
        return render(request, self.template_name, {"config": self._get_config()})

    def post(self, request):
        config = self._get_config()
        config.nombre   = request.POST.get("nombre", config.nombre)
        config.ip       = request.POST.get("ip", config.ip)
        config.puerto   = int(request.POST.get("puerto", config.puerto))
        config.protocolo= request.POST.get("protocolo", config.protocolo)
        config.usuario  = request.POST.get("usuario", config.usuario)
        config.puerta   = int(request.POST.get("puerta", config.puerta))
        config.minutos_expiracion_default = int(
            request.POST.get("minutos_expiracion_default", config.minutos_expiracion_default)
        )
        nueva_pw = request.POST.get("password", "").strip()
        if nueva_pw:
            config.password = nueva_pw
        config.save()
        messages.success(request, "Configuración guardada correctamente.")
        return redirect("hikvision_config")


class HikvisionTestView(SoloAdminMixin, View):
    """POST /qr/config/test/ — Probar conexión."""

    def post(self, request):
        config = ConfiguracionHikvision.objects.filter(activo=True).first()
        if not config:
            messages.error(request, "No hay configuración activa.")
            return redirect("hikvision_config")
        resultado = HikvisionService(config).probar_conexion()
        if resultado.exitoso:
            messages.success(request, f"✓ Conexión exitosa: {resultado.mensaje}")
        else:
            messages.error(request, f"✗ Error de conexión: {resultado.mensaje}")
        return redirect("hikvision_config")

"""
apps/accesos/views.py
======================
Endpoint público REST para validación de QR desde torniquetes.
"""

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qr_codes.models import EstadoTicket, TicketQR

from .models import Acceso, ResultadoAcceso


class ValidarQRAPIView(APIView):
    """
    POST /api/accesos/validar/
    Endpoint público para validación de QR desde lectores externos.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        contenido = request.data.get("contenido", "").strip()
        if not contenido:
            return Response({"resultado": "denegado", "razon": "Contenido vacío."}, status=400)

        ticket = TicketQR.objects.filter(codigo=contenido).first()
        ip = self._get_ip(request)

        if not ticket:
            Acceso.objects.create(
                qr_contenido=contenido, resultado=ResultadoAcceso.DENEGADO,
                razon="Código no registrado.", ip_address=ip
            )
            return Response({"resultado": "denegado", "razon": "Código no registrado."}, status=404)

        ahora = timezone.now()

        if ahora > ticket.fecha_expiracion:
            if ticket.estado == EstadoTicket.ACTIVO:
                ticket.estado = EstadoTicket.EXPIRADO
                ticket.save(update_fields=["estado"])
            Acceso.objects.create(
                qr_contenido=contenido, qr_code=ticket,
                resultado=ResultadoAcceso.DENEGADO, razon="Ticket expirado.", ip_address=ip
            )
            return Response({"resultado": "denegado", "razon": "Ticket expirado."}, status=403)

        if ticket.estado in (EstadoTicket.USADO, EstadoTicket.ERROR, EstadoTicket.EXPIRADO):
            Acceso.objects.create(
                qr_contenido=contenido, qr_code=ticket,
                resultado=ResultadoAcceso.DENEGADO,
                razon=f"Ticket {ticket.estado}.", ip_address=ip
            )
            return Response({"resultado": "denegado", "razon": f"Ticket {ticket.estado}."}, status=403)

        ticket.estado   = EstadoTicket.USADO
        ticket.fecha_uso = ahora
        ticket.save(update_fields=["estado", "fecha_uso"])

        Acceso.objects.create(
            qr_contenido=contenido, qr_code=ticket,
            resultado=ResultadoAcceso.PERMITIDO, razon="Acceso autorizado.", ip_address=ip
        )
        return Response({
            "resultado": "permitido",
            "tipo_ticket": ticket.tipo_ticket.nombre,
            "expira": ticket.fecha_expiracion,
        }, status=200)

    def _get_ip(self, request):
        x_fwd = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_fwd.split(",")[0].strip() if x_fwd else request.META.get("REMOTE_ADDR")

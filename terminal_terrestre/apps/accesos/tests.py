"""
Pruebas de integración — apps/accesos

Cubre el endpoint POST /api/accesos/validar/ (ValidarQRAPIView):
  - Contenido vacío             → 400
  - Código no registrado        → 404 + log denegado
  - Ticket válido               → 200, estado=USADO, log permitido
  - Ticket ya usado             → 403 + log denegado
  - Ticket expirado (por BD)    → 403, estado→EXPIRADO, log denegado
  - Ticket en estado ERROR      → 403
  - Doble uso del mismo ticket  → segundo intento denegado
  - IP desde X-Forwarded-For    → se registra correctamente
  - IP directa (REMOTE_ADDR)    → se registra correctamente
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.qr_codes.models import EstadoTicket, TicketQR
from apps.tickets.models import TipoTicket
from apps.usuarios.models import RolUsuario, Usuario

from .models import Acceso, ResultadoAcceso


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _crear_ticket(tipo, operador, estado=EstadoTicket.ACTIVO,
                  minutos=10, codigo=None, expirado=False):
    ahora = timezone.now()
    if expirado:
        inicio = ahora - timedelta(hours=2)
        expiracion = ahora - timedelta(hours=1)
    else:
        inicio = ahora
        expiracion = ahora + timedelta(minutes=minutos)

    return TicketQR.objects.create(
        codigo=codigo or f"QR{ahora.timestamp()}",
        tipo_ticket=tipo,
        precio=tipo.precio,
        minutos_expiracion=minutos,
        fecha_inicio=inicio,
        fecha_expiracion=expiracion,
        estado=estado,
        imagen_qr_base64="data:image/png;base64,abc",
        hik_usuario_ok=True,
        hik_tarjeta_ok=True,
        operador=operador,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class ValidarQRAPIViewTest(TestCase):
    """Pruebas de integración del endpoint de validación de QR."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("api_validar_qr")
        self.tipo = TipoTicket.objects.create(
            nombre="Interprovincial", precio=Decimal("2.00")
        )
        self.operador = Usuario.objects.create_user(
            username="op_acc", password="pass", rol=RolUsuario.OPERADOR
        )

    # ------------------------------------------------------------------
    # Validaciones de entrada
    # ------------------------------------------------------------------

    def test_contenido_vacio_retorna_400(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_contenido_espacios_retorna_400(self):
        resp = self.client.post(self.url, {"contenido": "   "}, format="json")
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # Código no registrado
    # ------------------------------------------------------------------

    def test_codigo_inexistente_retorna_404(self):
        resp = self.client.post(self.url, {"contenido": "NO_EXISTE"}, format="json")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.data["resultado"], "denegado")

    def test_codigo_inexistente_crea_log_denegado(self):
        self.client.post(self.url, {"contenido": "FAKE_CODE"}, format="json")
        self.assertEqual(Acceso.objects.count(), 1)
        self.assertEqual(Acceso.objects.first().resultado, ResultadoAcceso.DENEGADO)

    # ------------------------------------------------------------------
    # Ticket válido
    # ------------------------------------------------------------------

    def test_ticket_valido_retorna_200(self):
        _crear_ticket(self.tipo, self.operador, codigo="VALIDO_001")
        resp = self.client.post(self.url, {"contenido": "VALIDO_001"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["resultado"], "permitido")

    def test_ticket_valido_respuesta_incluye_tipo_ticket(self):
        _crear_ticket(self.tipo, self.operador, codigo="VALIDO_002")
        resp = self.client.post(self.url, {"contenido": "VALIDO_002"}, format="json")
        self.assertEqual(resp.data["tipo_ticket"], "Interprovincial")

    def test_ticket_valido_marca_estado_usado(self):
        ticket = _crear_ticket(self.tipo, self.operador, codigo="VALIDO_003")
        self.client.post(self.url, {"contenido": "VALIDO_003"}, format="json")
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado, EstadoTicket.USADO)

    def test_ticket_valido_registra_fecha_uso(self):
        ticket = _crear_ticket(self.tipo, self.operador, codigo="VALIDO_004")
        self.client.post(self.url, {"contenido": "VALIDO_004"}, format="json")
        ticket.refresh_from_db()
        self.assertIsNotNone(ticket.fecha_uso)

    def test_ticket_valido_crea_log_permitido(self):
        _crear_ticket(self.tipo, self.operador, codigo="VALIDO_005")
        self.client.post(self.url, {"contenido": "VALIDO_005"}, format="json")
        acceso = Acceso.objects.first()
        self.assertEqual(acceso.resultado, ResultadoAcceso.PERMITIDO)

    # ------------------------------------------------------------------
    # Ticket ya usado
    # ------------------------------------------------------------------

    def test_ticket_usado_retorna_403(self):
        _crear_ticket(self.tipo, self.operador, estado=EstadoTicket.USADO, codigo="USADO_001")
        resp = self.client.post(self.url, {"contenido": "USADO_001"}, format="json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.data["resultado"], "denegado")

    def test_doble_uso_segundo_intento_es_denegado(self):
        _crear_ticket(self.tipo, self.operador, codigo="DOBLE_001")
        self.client.post(self.url, {"contenido": "DOBLE_001"}, format="json")
        resp = self.client.post(self.url, {"contenido": "DOBLE_001"}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_doble_uso_genera_dos_logs(self):
        _crear_ticket(self.tipo, self.operador, codigo="DOBLE_002")
        self.client.post(self.url, {"contenido": "DOBLE_002"}, format="json")
        self.client.post(self.url, {"contenido": "DOBLE_002"}, format="json")
        self.assertEqual(Acceso.objects.count(), 2)

    # ------------------------------------------------------------------
    # Ticket expirado
    # ------------------------------------------------------------------

    def test_ticket_expirado_retorna_403(self):
        _crear_ticket(self.tipo, self.operador, codigo="EXP_001", expirado=True)
        resp = self.client.post(self.url, {"contenido": "EXP_001"}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_ticket_expirado_actualiza_estado_a_expirado(self):
        ticket = _crear_ticket(self.tipo, self.operador, codigo="EXP_002", expirado=True)
        self.client.post(self.url, {"contenido": "EXP_002"}, format="json")
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado, EstadoTicket.EXPIRADO)

    def test_ticket_ya_marcado_expirado_retorna_403(self):
        _crear_ticket(self.tipo, self.operador,
                      estado=EstadoTicket.EXPIRADO, codigo="EXP_003", expirado=True)
        resp = self.client.post(self.url, {"contenido": "EXP_003"}, format="json")
        self.assertEqual(resp.status_code, 403)

    # ------------------------------------------------------------------
    # Ticket en estado ERROR
    # ------------------------------------------------------------------

    def test_ticket_error_retorna_403(self):
        _crear_ticket(self.tipo, self.operador, estado=EstadoTicket.ERROR, codigo="ERR_001")
        resp = self.client.post(self.url, {"contenido": "ERR_001"}, format="json")
        self.assertEqual(resp.status_code, 403)

    # ------------------------------------------------------------------
    # Registro de IP
    # ------------------------------------------------------------------

    def test_ip_desde_x_forwarded_for(self):
        _crear_ticket(self.tipo, self.operador, codigo="IP_001")
        self.client.post(
            self.url,
            {"contenido": "IP_001"},
            format="json",
            HTTP_X_FORWARDED_FOR="10.0.0.5, 192.168.1.1",
        )
        acceso = Acceso.objects.first()
        self.assertEqual(acceso.ip_address, "10.0.0.5")

    def test_ip_desde_remote_addr(self):
        _crear_ticket(self.tipo, self.operador, codigo="IP_002")
        self.client.post(
            self.url,
            {"contenido": "IP_002"},
            format="json",
            REMOTE_ADDR="172.16.0.1",
        )
        acceso = Acceso.objects.first()
        self.assertEqual(acceso.ip_address, "172.16.0.1")

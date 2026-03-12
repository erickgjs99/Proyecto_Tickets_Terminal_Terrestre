"""
Pruebas unitarias e integrales — apps/qr_codes

Unitarias:
  - generar_qr_base64
  - HikvisionService._fmt_local
  - HikvisionService._request (HTTP mockeado)
  - HikvisionService.crear_pase_completo (flujo interno)

Integrales:
  - GenerarTicketView: Hikvision falla → no se crea ticket
  - GenerarTicketView: Hikvision OK → se crea ticket y venta
"""

import base64
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import requests as req_lib
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.tickets.models import TipoTicket
from apps.usuarios.models import RolUsuario, Usuario
from apps.ventas.models import Venta

from .models import ConfiguracionHikvision, EstadoTicket, TicketQR
from .services import HikvisionService, ResultadoHikvision, generar_qr_base64


# ===========================================================================
# Utilidades QR
# ===========================================================================

class GenerarQRBase64Test(TestCase):
    """Pruebas unitarias de la función generar_qr_base64."""

    def test_retorna_data_uri_png(self):
        resultado = generar_qr_base64("1234567890")
        self.assertTrue(resultado.startswith("data:image/png;base64,"))

    def test_base64_decodificable(self):
        resultado = generar_qr_base64("test_codigo")
        _, datos = resultado.split(",", 1)
        # No debe lanzar excepción
        decodificado = base64.b64decode(datos)
        self.assertGreater(len(decodificado), 0)

    def test_contenidos_distintos_generan_imagenes_distintas(self):
        qr1 = generar_qr_base64("codigo_a")
        qr2 = generar_qr_base64("codigo_b")
        self.assertNotEqual(qr1, qr2)

    def test_mismo_contenido_genera_misma_imagen(self):
        qr1 = generar_qr_base64("igual")
        qr2 = generar_qr_base64("igual")
        self.assertEqual(qr1, qr2)


# ===========================================================================
# HikvisionService — _fmt_local
# ===========================================================================

class HikvisionFmtLocalTest(TestCase):
    """Pruebas unitarias del formateador de fecha ISAPI."""

    def setUp(self):
        config = MagicMock()
        config.url_base = "http://192.168.1.1"
        config.usuario = "admin"
        config.password = "admin"
        config.puerta = 1
        self.svc = HikvisionService(config)

    def test_datetime_naive_se_formatea_correctamente(self):
        dt = datetime(2024, 6, 1, 12, 30, 0)
        self.assertEqual(self.svc._fmt_local(dt), "2024-06-01T12:30:00")

    def test_datetime_aware_retorna_formato_isapi(self):
        dt = timezone.now()
        resultado = self.svc._fmt_local(dt)
        import re
        self.assertRegex(resultado, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


# ===========================================================================
# HikvisionService — _request (HTTP mockeado)
# ===========================================================================

class HikvisionRequestTest(TestCase):
    """Pruebas del método _request con HTTP completamente mockeado."""

    def setUp(self):
        config = MagicMock()
        config.url_base = "http://192.168.1.1"
        config.usuario = "admin"
        config.password = "admin"
        config.puerta = 1
        self.svc = HikvisionService(config)

    @patch("apps.qr_codes.services.requests.request")
    def test_exitoso_con_statuscode_1(self, mock_req):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"statusCode": 1, "statusString": "OK"}
        resp.text = '{"statusCode": 1, "statusString": "OK"}'
        mock_req.return_value = resp

        resultado = self.svc._request("POST", "http://x/ep", {})

        self.assertTrue(resultado.exitoso)
        self.assertEqual(resultado.codigo_status, 200)

    @patch("apps.qr_codes.services.requests.request")
    def test_falla_con_statuscode_distinto_de_1(self, mock_req):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"statusCode": 4, "statusString": "deviceBusy"}
        resp.text = '{"statusCode": 4}'
        mock_req.return_value = resp

        resultado = self.svc._request("POST", "http://x/ep", {})

        self.assertFalse(resultado.exitoso)

    @patch("apps.qr_codes.services.requests.request")
    def test_falla_con_http_500(self, mock_req):
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "Internal Server Error"
        mock_req.return_value = resp

        resultado = self.svc._request("POST", "http://x/ep", {})

        self.assertFalse(resultado.exitoso)
        self.assertEqual(resultado.codigo_status, 500)

    @patch("apps.qr_codes.services.requests.request")
    def test_connection_error_retorna_exitoso_false(self, mock_req):
        mock_req.side_effect = req_lib.exceptions.ConnectionError("no route")

        resultado = self.svc._request("POST", "http://x/ep", {})

        self.assertFalse(resultado.exitoso)
        self.assertEqual(resultado.codigo_status, 0)

    @patch("apps.qr_codes.services.requests.request")
    def test_timeout_retorna_mensaje_agotado(self, mock_req):
        mock_req.side_effect = req_lib.exceptions.Timeout()

        resultado = self.svc._request("POST", "http://x/ep", {})

        self.assertFalse(resultado.exitoso)
        self.assertIn("agotado", resultado.mensaje)


# ===========================================================================
# HikvisionService — crear_pase_completo
# ===========================================================================

class HikvisionCrearPaseTest(TestCase):
    """Pruebas del flujo crear_pase_completo."""

    def setUp(self):
        config = MagicMock()
        config.url_base = "http://192.168.1.1"
        config.usuario = "admin"
        config.password = "admin"
        config.puerta = 1
        self.svc = HikvisionService(config)
        self.ahora = timezone.now()
        self.expira = self.ahora + timedelta(minutes=10)

    def _res_ok(self):
        return ResultadoHikvision(
            exitoso=True, codigo_status=200,
            mensaje="OK", respuesta_raw='{"statusCode":1}'
        )

    def _res_fallo(self):
        return ResultadoHikvision(
            exitoso=False, codigo_status=0,
            mensaje="Error", respuesta_raw=""
        )

    def test_si_usuario_falla_no_se_intenta_tarjeta(self):
        with patch.object(self.svc, "crear_usuario_temporal", return_value=self._res_fallo()):
            with patch.object(self.svc, "asignar_tarjeta_qr") as mock_tarjeta:
                res_u, res_t = self.svc.crear_pase_completo("EMP001", self.ahora, self.expira)

        mock_tarjeta.assert_not_called()
        self.assertFalse(res_u.exitoso)
        self.assertFalse(res_t.exitoso)

    def test_si_usuario_ok_se_intenta_tarjeta(self):
        with patch.object(self.svc, "crear_usuario_temporal", return_value=self._res_ok()):
            with patch.object(self.svc, "asignar_tarjeta_qr", return_value=self._res_ok()) as mock_tarjeta:
                res_u, res_t = self.svc.crear_pase_completo("EMP002", self.ahora, self.expira)

        mock_tarjeta.assert_called_once_with("EMP002")
        self.assertTrue(res_u.exitoso)
        self.assertTrue(res_t.exitoso)

    def test_resultado_tuple_tiene_dos_elementos(self):
        with patch.object(self.svc, "crear_usuario_temporal", return_value=self._res_ok()):
            with patch.object(self.svc, "asignar_tarjeta_qr", return_value=self._res_ok()):
                resultado = self.svc.crear_pase_completo("EMP003", self.ahora, self.expira)

        self.assertEqual(len(resultado), 2)


# ===========================================================================
# GenerarTicketView — Tests de integración
# ===========================================================================

def _res_hik_ok():
    return ResultadoHikvision(
        exitoso=True, codigo_status=200,
        mensaje="OK", respuesta_raw='{"statusCode":1}'
    )


def _res_hik_fallo():
    return ResultadoHikvision(
        exitoso=False, codigo_status=0,
        mensaje="Sin conexión", respuesta_raw=""
    )


class GenerarTicketViewTest(TestCase):
    """Pruebas de integración para la vista GenerarTicketView."""

    def setUp(self):
        self.client = Client()
        self.operador = Usuario.objects.create_user(
            username="op_view", password="pass123", rol=RolUsuario.OPERADOR
        )
        self.tipo = TipoTicket.objects.create(
            nombre="Interprovincial Test", precio=Decimal("2.00"), prefijo="INT"
        )
        # Permitir al operador generar este tipo de ticket
        self.operador.tipos_ticket_permitidos.add(self.tipo)

        self.config = ConfiguracionHikvision.objects.create(
            nombre="Test Device",
            ip="192.168.1.1",
            puerto=80,
            usuario="admin",
            password="admin",
            puerta=1,
            activo=True,
        )
        self.url = reverse("qr_generar")
        self.client.login(username="op_view", password="pass123")

    def _post(self, tipo_id=None, minutos=10):
        return self.client.post(self.url, {
            "tipo_ticket": tipo_id or self.tipo.id,
            "minutos_expiracion": minutos,
        })

    # ------------------------------------------------------------------
    # Hikvision falla → no se crea nada
    # ------------------------------------------------------------------

    @patch("apps.qr_codes.views.HikvisionService.crear_pase_completo")
    def test_hikvision_falla_no_crea_ticket(self, mock_pase):
        mock_pase.return_value = (_res_hik_fallo(), _res_hik_fallo())

        self._post()

        self.assertEqual(TicketQR.objects.count(), 0)
        self.assertEqual(Venta.objects.count(), 0)

    @patch("apps.qr_codes.views.HikvisionService.crear_pase_completo")
    def test_hikvision_falla_muestra_mensaje_error(self, mock_pase):
        mock_pase.return_value = (_res_hik_fallo(), _res_hik_fallo())

        resp = self._post()

        messages = list(resp.wsgi_request._messages)
        self.assertTrue(any("Hikvision" in str(m) for m in messages))

    @patch("apps.qr_codes.views.HikvisionService.crear_pase_completo")
    def test_hikvision_falla_usuario_ok_tarjeta_falla_no_crea_ticket(self, mock_pase):
        """Si el usuario se crea pero la tarjeta falla, tampoco se crea nada."""
        mock_pase.return_value = (_res_hik_ok(), _res_hik_fallo())

        self._post()

        self.assertEqual(TicketQR.objects.count(), 0)

    # ------------------------------------------------------------------
    # Hikvision OK → se crea ticket y venta
    # ------------------------------------------------------------------

    @patch("apps.qr_codes.views.HikvisionService.crear_pase_completo")
    def test_hikvision_ok_crea_ticket_qr(self, mock_pase):
        mock_pase.return_value = (_res_hik_ok(), _res_hik_ok())

        self._post()

        self.assertEqual(TicketQR.objects.count(), 1)

    @patch("apps.qr_codes.views.HikvisionService.crear_pase_completo")
    def test_hikvision_ok_crea_venta(self, mock_pase):
        mock_pase.return_value = (_res_hik_ok(), _res_hik_ok())

        self._post()

        self.assertEqual(Venta.objects.count(), 1)

    @patch("apps.qr_codes.views.HikvisionService.crear_pase_completo")
    def test_hikvision_ok_ticket_estado_activo(self, mock_pase):
        mock_pase.return_value = (_res_hik_ok(), _res_hik_ok())

        self._post()

        ticket = TicketQR.objects.first()
        self.assertEqual(ticket.estado, EstadoTicket.ACTIVO)

    @patch("apps.qr_codes.views.HikvisionService.crear_pase_completo")
    def test_hikvision_ok_precio_correcto(self, mock_pase):
        mock_pase.return_value = (_res_hik_ok(), _res_hik_ok())

        self._post()

        ticket = TicketQR.objects.first()
        self.assertEqual(ticket.precio, Decimal("2.00"))

    @patch("apps.qr_codes.views.HikvisionService.crear_pase_completo")
    def test_hikvision_ok_venta_tiene_numero_ticket(self, mock_pase):
        mock_pase.return_value = (_res_hik_ok(), _res_hik_ok())

        self._post()

        venta = Venta.objects.first()
        self.assertIsNotNone(venta.numero_ticket)
        self.assertTrue(venta.numero_ticket.startswith("INT-"))

    # ------------------------------------------------------------------
    # Acceso sin login
    # ------------------------------------------------------------------

    def test_sin_login_redirige_a_login(self):
        self.client.logout()
        resp = self._post()
        self.assertIn("/login/", resp["Location"])

    # ------------------------------------------------------------------
    # Tipo inválido
    # ------------------------------------------------------------------

    @patch("apps.qr_codes.views.HikvisionService.crear_pase_completo")
    def test_tipo_ticket_invalido_no_crea_nada(self, mock_pase):
        mock_pase.return_value = (_res_hik_ok(), _res_hik_ok())

        resp = self.client.post(self.url, {
            "tipo_ticket": 9999,
            "minutos_expiracion": 10,
        })

        self.assertEqual(TicketQR.objects.count(), 0)
        mock_pase.assert_not_called()

    # ------------------------------------------------------------------
    # Sin configuración Hikvision
    # ------------------------------------------------------------------

    def test_sin_config_hikvision_no_crea_ticket(self):
        self.config.activo = False
        self.config.save()

        self._post()

        self.assertEqual(TicketQR.objects.count(), 0)

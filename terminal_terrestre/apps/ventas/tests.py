"""
Pruebas unitarias e integrales — apps/ventas
Enfocadas en la numeración secuencial de tickets.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.qr_codes.models import EstadoTicket, TicketQR
from apps.tickets.models import TipoTicket
from apps.usuarios.models import RolUsuario, Usuario

from .models import Venta


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _crear_ticket_qr(tipo, operador, codigo=None):
    ahora = timezone.now()
    return TicketQR.objects.create(
        codigo=codigo or f"test_{ahora.timestamp()}_{tipo.id}",
        tipo_ticket=tipo,
        precio=tipo.precio,
        minutos_expiracion=10,
        fecha_inicio=ahora,
        fecha_expiracion=ahora + timedelta(minutes=10),
        estado=EstadoTicket.ACTIVO,
        imagen_qr_base64="data:image/png;base64,abc",
        hik_usuario_ok=True,
        hik_tarjeta_ok=True,
        operador=operador,
    )


def _crear_venta(tipo, operador):
    ticket = _crear_ticket_qr(tipo, operador)
    return Venta.objects.create(
        ticket_qr=ticket,
        tipo_ticket=tipo,
        precio=tipo.precio,
        operador=operador,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class NumeracionSecuencialTest(TestCase):
    """Verifica que los números de ticket sean secuenciales y por tipo."""

    def setUp(self):
        self.tipo = TipoTicket.objects.create(
            nombre="Test Tipo", precio=Decimal("1.00"), prefijo="TST"
        )
        self.operador = Usuario.objects.create_user(
            username="op_ventas", password="pass", rol=RolUsuario.OPERADOR
        )

    def test_primer_ticket_es_000001(self):
        venta = _crear_venta(self.tipo, self.operador)
        self.assertEqual(venta.numero_ticket, "TST-000001")

    def test_segundo_ticket_es_000002(self):
        _crear_venta(self.tipo, self.operador)
        venta2 = _crear_venta(self.tipo, self.operador)
        self.assertEqual(venta2.numero_ticket, "TST-000002")

    def test_tercero_ticket_es_000003(self):
        for _ in range(2):
            _crear_venta(self.tipo, self.operador)
        venta3 = _crear_venta(self.tipo, self.operador)
        self.assertEqual(venta3.numero_ticket, "TST-000003")

    def test_secuencia_es_independiente_por_tipo(self):
        """Cada tipo de ticket tiene su propia secuencia."""
        tipo2 = TipoTicket.objects.create(
            nombre="Otro Tipo", precio=Decimal("0.50"), prefijo="OTR"
        )
        _crear_venta(self.tipo, self.operador)
        _crear_venta(self.tipo, self.operador)

        # Primer ticket del segundo tipo debe ser OTR-000001
        venta_otro = _crear_venta(tipo2, self.operador)
        self.assertEqual(venta_otro.numero_ticket, "OTR-000001")

    def test_prefijo_se_convierte_a_mayusculas(self):
        tipo_lower = TipoTicket.objects.create(
            nombre="Lower Prefijo", precio=Decimal("0.25"), prefijo="low"
        )
        venta = _crear_venta(tipo_lower, self.operador)
        self.assertTrue(venta.numero_ticket.startswith("LOW-"))

    def test_numero_no_se_reasigna_en_update(self):
        """Guardar de nuevo una venta existente no debe cambiar el número."""
        venta = _crear_venta(self.tipo, self.operador)
        numero_original = venta.numero_ticket
        venta.observaciones = "actualizado"
        venta.save()
        self.assertEqual(venta.numero_ticket, numero_original)

    def test_str_incluye_numero_tipo_y_precio(self):
        venta = _crear_venta(self.tipo, self.operador)
        s = str(venta)
        self.assertIn("TST-000001", s)
        self.assertIn("Test Tipo", s)

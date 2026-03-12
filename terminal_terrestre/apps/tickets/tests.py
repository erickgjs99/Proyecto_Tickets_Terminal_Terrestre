"""
Pruebas unitarias — apps/tickets
"""

from decimal import Decimal

from django.test import TestCase

from .models import TipoTicket


class TipoTicketModelTest(TestCase):
    """Pruebas del modelo TipoTicket."""

    def setUp(self):
        self.ticket = TipoTicket.objects.create(
            nombre="Interprovinciales",
            precio=Decimal("2.00"),
            prefijo="INT",
        )

    # ------------------------------------------------------------------
    # Valores por defecto
    # ------------------------------------------------------------------

    def test_activo_default_true(self):
        self.assertTrue(self.ticket.activo)

    def test_prefijo_default_tk(self):
        tk = TipoTicket.objects.create(nombre="Sin Prefijo", precio=Decimal("1.00"))
        self.assertEqual(tk.prefijo, "TK")

    def test_str_incluye_nombre_y_precio(self):
        self.assertIn("Interprovinciales", str(self.ticket))
        self.assertIn("2.00", str(self.ticket))

    # ------------------------------------------------------------------
    # Precios decimales menores a 1
    # ------------------------------------------------------------------

    def test_precio_centavos_se_guarda_correctamente(self):
        tk = TipoTicket.objects.create(nombre="Pasajeros", precio=Decimal("0.10"))
        tk.refresh_from_db()
        self.assertEqual(tk.precio, Decimal("0.10"))

    def test_precio_menos_de_un_dolar(self):
        tk = TipoTicket.objects.create(nombre="Tercera Edad", precio=Decimal("0.05"))
        tk.refresh_from_db()
        self.assertEqual(tk.precio, Decimal("0.05"))

    def test_precio_25_centavos(self):
        tk = TipoTicket.objects.create(nombre="Camioneta", precio=Decimal("0.25"))
        tk.refresh_from_db()
        self.assertEqual(tk.precio, Decimal("0.25"))

    # ------------------------------------------------------------------
    # Unicidad
    # ------------------------------------------------------------------

    def test_nombre_unico(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            TipoTicket.objects.create(nombre="Interprovinciales", precio=Decimal("1.00"))

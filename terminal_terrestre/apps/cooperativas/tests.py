"""
Pruebas unitarias — apps/cooperativas
"""

from django.test import TestCase

from .models import Cooperativa, EstadoCooperativa


class CooperativaModelTest(TestCase):
    """Pruebas del modelo Cooperativa."""

    def setUp(self):
        self.sin_limite = Cooperativa.objects.create(
            nombre="Sin Límite", max_boletos=0, boletos_utilizados=0
        )
        self.con_boletos = Cooperativa.objects.create(
            nombre="Con Boletos", max_boletos=10, boletos_utilizados=5
        )
        self.agotada = Cooperativa.objects.create(
            nombre="Agotada", max_boletos=5, boletos_utilizados=5
        )

    # ------------------------------------------------------------------
    # tiene_boletos_disponibles
    # ------------------------------------------------------------------

    def test_max_cero_siempre_disponible(self):
        """max_boletos=0 significa sin límite → siempre disponible."""
        self.assertTrue(self.sin_limite.tiene_boletos_disponibles)

    def test_con_cupo_disponible(self):
        self.assertTrue(self.con_boletos.tiene_boletos_disponibles)

    def test_sin_cupo_disponible(self):
        self.assertFalse(self.agotada.tiene_boletos_disponibles)

    def test_limite_exacto_no_disponible(self):
        coop = Cooperativa.objects.create(
            nombre="Exacta", max_boletos=3, boletos_utilizados=3
        )
        self.assertFalse(coop.tiene_boletos_disponibles)

    def test_uno_antes_del_limite_disponible(self):
        coop = Cooperativa.objects.create(
            nombre="Casi", max_boletos=3, boletos_utilizados=2
        )
        self.assertTrue(coop.tiene_boletos_disponibles)

    # ------------------------------------------------------------------
    # Estado y __str__
    # ------------------------------------------------------------------

    def test_estado_default_es_activo(self):
        self.assertEqual(self.sin_limite.estado, EstadoCooperativa.ACTIVO)

    def test_str_es_nombre(self):
        self.assertEqual(str(self.sin_limite), "Sin Límite")

    def test_nombre_unico(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Cooperativa.objects.create(nombre="Sin Límite", max_boletos=0)

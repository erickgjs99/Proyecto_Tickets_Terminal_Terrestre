"""
Pruebas unitarias — apps/usuarios
"""

from django.test import TestCase

from .models import RolUsuario, Usuario


class UsuarioRolesTest(TestCase):
    """Pruebas de las propiedades de rol del modelo Usuario."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username="admin_t", password="pass", rol=RolUsuario.ADMIN
        )
        self.operador = Usuario.objects.create_user(
            username="op_t", password="pass", rol=RolUsuario.OPERADOR
        )
        self.supervisor = Usuario.objects.create_user(
            username="sup_t", password="pass", rol=RolUsuario.SUPERVISOR
        )

    # ------------------------------------------------------------------
    # es_admin
    # ------------------------------------------------------------------

    def test_admin_es_admin(self):
        self.assertTrue(self.admin.es_admin)

    def test_operador_no_es_admin(self):
        self.assertFalse(self.operador.es_admin)

    def test_supervisor_no_es_admin(self):
        self.assertFalse(self.supervisor.es_admin)

    # ------------------------------------------------------------------
    # es_operador
    # ------------------------------------------------------------------

    def test_operador_es_operador(self):
        self.assertTrue(self.operador.es_operador)

    def test_admin_no_es_operador(self):
        self.assertFalse(self.admin.es_operador)

    def test_supervisor_no_es_operador(self):
        self.assertFalse(self.supervisor.es_operador)

    # ------------------------------------------------------------------
    # es_supervisor
    # ------------------------------------------------------------------

    def test_supervisor_es_supervisor(self):
        self.assertTrue(self.supervisor.es_supervisor)

    def test_admin_no_es_supervisor(self):
        self.assertFalse(self.admin.es_supervisor)

    def test_operador_no_es_supervisor(self):
        self.assertFalse(self.operador.es_supervisor)

    # ------------------------------------------------------------------
    # Rol por defecto
    # ------------------------------------------------------------------

    def test_rol_default_es_operador(self):
        usuario = Usuario.objects.create_user(username="nuevo", password="pass")
        self.assertEqual(usuario.rol, RolUsuario.OPERADOR)

    def test_activo_default_true(self):
        usuario = Usuario.objects.create_user(username="activo_t", password="pass")
        self.assertTrue(usuario.activo)

    def test_str_incluye_rol(self):
        self.assertIn("Administrador", str(self.admin))

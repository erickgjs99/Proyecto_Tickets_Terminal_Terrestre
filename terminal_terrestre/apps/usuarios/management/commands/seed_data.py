"""
apps/usuarios/management/commands/seed_data.py
===============================================
Comando para poblar la base de datos con datos iniciales reales del
Terminal Terrestre "Mons. Santiago Fernández García" de Cariamanga.

Uso:
    python manage.py seed_data
"""

from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from apps.cooperativas.models import Cooperativa
from apps.qr_codes.models import ConfiguracionHikvision
from apps.tickets.models import TipoTicket
from apps.usuarios.models import RolUsuario, Usuario


class Command(BaseCommand):
    help = "Carga datos iniciales del Terminal Terrestre de Cariamanga."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("═" * 55))
        self.stdout.write(self.style.MIGRATE_HEADING("  Terminal Terrestre — Carga de datos iniciales"))
        self.stdout.write(self.style.MIGRATE_HEADING("═" * 55))

        self._crear_usuarios()
        self._crear_tipos_ticket()
        self._crear_cooperativas()
        self._crear_configuracion_hikvision()

        self.stdout.write(self.style.SUCCESS("\n✓ Datos iniciales cargados correctamente.\n"))

    # ------------------------------------------------------------------
    # Usuarios
    # ------------------------------------------------------------------
    def _crear_usuarios(self):
        self.stdout.write("\n[1/4] Creando usuarios...")

        usuarios = [
            {
                "username": "admin",
                "password": "admin123",
                "first_name": "Administrador",
                "last_name": "Sistema",
                "email": "admin@terminal.gob.ec",
                "rol": RolUsuario.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "maria",
                "password": "operador123",
                "first_name": "María",
                "last_name": "González",
                "email": "maria@terminal.gob.ec",
                "rol": RolUsuario.OPERADOR,
            },
            {
                "username": "juan",
                "password": "operador123",
                "first_name": "Juan",
                "last_name": "Pérez",
                "email": "juan@terminal.gob.ec",
                "rol": RolUsuario.OPERADOR,
            },
            {
                "username": "pedro",
                "password": "operador123",
                "first_name": "Pedro",
                "last_name": "Rodríguez",
                "email": "pedro@terminal.gob.ec",
                "rol": RolUsuario.OPERADOR,
            },
            {
                "username": "ana",
                "password": "supervisor123",
                "first_name": "Ana",
                "last_name": "Administradora",
                "email": "ana@terminal.gob.ec",
                "rol": RolUsuario.SUPERVISOR,
            },
        ]

        for datos in usuarios:
            password = datos.pop("password")
            usuario, creado = Usuario.objects.get_or_create(
                username=datos["username"],
                defaults=datos,
            )
            if creado:
                usuario.set_password(password)
                usuario.save()
                self.stdout.write(f"  ✓ {usuario.username} ({usuario.get_rol_display()})")
            else:
                self.stdout.write(f"  · {usuario.username} ya existe")

    # ------------------------------------------------------------------
    # Tipos de ticket
    # ------------------------------------------------------------------
    def _crear_tipos_ticket(self):
        self.stdout.write("\n[2/4] Creando tipos de ticket...")

        tipos = [
            {
                "nombre": "Interprovinciales",
                "precio": Decimal("2.00"),
                "descripcion": "Buses interprovinciales",
            },
            {
                "nombre": "Intraprovinciales",
                "precio": Decimal("1.00"),
                "descripcion": "Buses intraprovinciales",
            },
            {
                "nombre": "Garaje",
                "precio": Decimal("1.00"),
                "descripcion": "Uso de garaje del terminal",
            },
            {
                "nombre": "Intracantonal - Rancheras",
                "precio": Decimal("0.50"),
                "descripcion": "Buses intracantonales y rancheras",
            },
            {
                "nombre": "Camionetas",
                "precio": Decimal("0.25"),
                "descripcion": "Camionetas de servicio",
            },
            {
                "nombre": "Pasajeros",
                "precio": Decimal("0.10"),
                "descripcion": "Tasa de uso terminal por pasajero",
            },
            {
                "nombre": "3era. Edad / Discapacidad",
                "precio": Decimal("0.05"),
                "descripcion": "Tarifa preferencial tercera edad y personas con discapacidad",
            },
        ]

        for datos in tipos:
            tipo, creado = TipoTicket.objects.get_or_create(
                nombre=datos["nombre"],
                defaults=datos,
            )
            if creado:
                self.stdout.write(f"  ✓ {tipo.nombre} — ${tipo.precio}")
            else:
                self.stdout.write(f"  · {tipo.nombre} ya existe")

    # ------------------------------------------------------------------
    # Cooperativas
    # ------------------------------------------------------------------
    def _crear_cooperativas(self):
        self.stdout.write("\n[3/4] Creando cooperativas...")

        cooperativas = [
            {"nombre": "Flota Imbabura", "max_boletos": 0},
            {"nombre": "Trans Esmeraldas", "max_boletos": 0},
            {"nombre": "Reina del Camino", "max_boletos": 0},
            {"nombre": "Pullman Carchi", "max_boletos": 0},
        ]

        for datos in cooperativas:
            coop, creado = Cooperativa.objects.get_or_create(
                nombre=datos["nombre"],
                defaults=datos,
            )
            if creado:
                self.stdout.write(f"  ✓ {coop.nombre}")
            else:
                self.stdout.write(f"  · {coop.nombre} ya existe")

    # ------------------------------------------------------------------
    # Configuración Hikvision
    # ------------------------------------------------------------------
    def _crear_configuracion_hikvision(self):
        self.stdout.write("\n[4/4] Configurando Hikvision...")

        config, creado = ConfiguracionHikvision.objects.get_or_create(
            activo=True,
            defaults={
                "nombre": "Torniquete Principal",
                "ip": "172.168.109.5",
                "puerto": 80,
                "protocolo": "http",
                "usuario": "admin",
                "password": "admin",  # Cambiar en producción
                "puerta": 1,
                "minutos_expiracion_default": 10,
            },
        )

        if creado:
            self.stdout.write(f"  ✓ {config.nombre} → {config.url_base}")
        else:
            self.stdout.write(f"  · Configuración ya existe: {config.url_base}")

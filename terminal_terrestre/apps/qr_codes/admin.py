from django.contrib import admin
from .models import ConfiguracionHikvision, TicketQR


@admin.register(ConfiguracionHikvision)
class ConfiguracionHikvisionAdmin(admin.ModelAdmin):
    list_display = ["nombre", "ip", "puerto", "puerta", "activo", "fecha_actualizacion"]


@admin.register(TicketQR)
class TicketQRAdmin(admin.ModelAdmin):
    list_display = [
        "codigo", "tipo_ticket", "precio", "estado",
        "hik_usuario_ok", "hik_tarjeta_ok", "operador", "fecha_creacion",
    ]
    list_filter = ["estado", "tipo_ticket", "hik_usuario_ok", "hik_tarjeta_ok"]
    search_fields = ["codigo"]
    readonly_fields = ["imagen_qr_base64", "hik_respuesta", "fecha_creacion"]
    date_hierarchy = "fecha_creacion"

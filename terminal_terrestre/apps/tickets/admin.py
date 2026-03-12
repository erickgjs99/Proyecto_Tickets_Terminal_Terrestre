from django.contrib import admin
from .models import TipoTicket

@admin.register(TipoTicket)
class TipoTicketAdmin(admin.ModelAdmin):
    list_display = ["nombre", "precio", "activo", "fecha_creacion"]
    list_filter = ["activo"]
    search_fields = ["nombre"]

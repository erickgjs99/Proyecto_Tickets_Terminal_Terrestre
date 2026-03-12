from django.contrib import admin
from .models import Venta

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ["numero_ticket", "tipo_ticket", "precio", "cooperativa", "operador", "fecha"]
    list_filter = ["tipo_ticket", "cooperativa", "operador"]
    search_fields = ["numero_ticket"]
    date_hierarchy = "fecha"
    readonly_fields = ["numero_ticket", "fecha"]

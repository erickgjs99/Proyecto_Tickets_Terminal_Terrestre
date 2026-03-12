from django.contrib import admin
from .models import Acceso

@admin.register(Acceso)
class AccesoAdmin(admin.ModelAdmin):
    list_display = ["fecha", "qr_contenido", "resultado", "razon", "ip_address"]
    list_filter = ["resultado"]
    date_hierarchy = "fecha"

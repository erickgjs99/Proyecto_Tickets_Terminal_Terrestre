from django.contrib import admin
from .models import Cooperativa

@admin.register(Cooperativa)
class CooperativaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "estado", "max_boletos", "boletos_utilizados"]
    list_filter = ["estado"]
    search_fields = ["nombre"]

"""apps/tickets/views.py"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from apps.usuarios.mixins import SoloAdminMixin
from .models import TipoTicket


class TiposTicketListView(LoginRequiredMixin, View):
    template_name = "tickets/tipos_lista.html"

    def get(self, request):
        return render(request, self.template_name, {
            "tipos": TipoTicket.objects.all()
        })


class TipoTicketCreateView(SoloAdminMixin, View):
    def post(self, request):
        nombre = request.POST.get("nombre", "").strip()
        prefijo = request.POST.get("prefijo", "TK").strip().upper()
        precio = request.POST.get("precio")
        descripcion = request.POST.get("descripcion", "")
        activo = request.POST.get("activo", "true") == "true"

        if not nombre or not precio or not prefijo:
            messages.error(request, "Nombre, prefijo y precio son obligatorios.")
        else:
            TipoTicket.objects.create(
                nombre=nombre, prefijo=prefijo, precio=precio,
                descripcion=descripcion, activo=activo
            )
            messages.success(request, f"Tipo '{nombre}' ({prefijo}) creado correctamente.")
        return redirect("tipos_ticket")


class TipoTicketEditView(SoloAdminMixin, View):
    def post(self, request, pk):
        try:
            tipo = TipoTicket.objects.get(pk=pk)
        except TipoTicket.DoesNotExist:
            messages.error(request, "Tipo de ticket no encontrado.")
            return redirect("tipos_ticket")

        tipo.nombre      = request.POST.get("nombre", tipo.nombre)
        tipo.prefijo     = request.POST.get("prefijo", tipo.prefijo).strip().upper()
        tipo.precio      = request.POST.get("precio", tipo.precio)
        tipo.descripcion = request.POST.get("descripcion", tipo.descripcion)
        tipo.activo      = request.POST.get("activo", "true") == "true"
        tipo.save()
        messages.success(request, f"Tipo '{tipo.nombre}' actualizado.")
        return redirect("tipos_ticket")


class TipoTicketDeleteView(SoloAdminMixin, View):
    def post(self, request, pk):
        try:
            tipo = TipoTicket.objects.get(pk=pk)
            nombre = tipo.nombre
            tipo.delete()
            messages.success(request, f"Tipo '{nombre}' eliminado.")
        except TipoTicket.DoesNotExist:
            messages.error(request, "Tipo no encontrado.")
        return redirect("tipos_ticket")

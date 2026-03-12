"""apps/cooperativas/views.py"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from apps.usuarios.mixins import SoloAdminMixin
from .models import Cooperativa


class CooperativasListView(LoginRequiredMixin, View):
    template_name = "cooperativas/cooperativas_lista.html"

    def get(self, request):
        return render(request, self.template_name, {
            "cooperativas": Cooperativa.objects.all()
        })


class CooperativaCreateView(SoloAdminMixin, View):
    def post(self, request):
        nombre = request.POST.get("nombre", "").strip()
        if not nombre:
            messages.error(request, "El nombre es obligatorio.")
        else:
            Cooperativa.objects.create(
                nombre=nombre,
                max_boletos=int(request.POST.get("max_boletos", 0)),
                estado=request.POST.get("estado", "activo"),
            )
            messages.success(request, f"Cooperativa '{nombre}' creada.")
        return redirect("cooperativas")


class CooperativaEditView(SoloAdminMixin, View):
    def post(self, request, pk):
        try:
            coop = Cooperativa.objects.get(pk=pk)
        except Cooperativa.DoesNotExist:
            messages.error(request, "Cooperativa no encontrada.")
            return redirect("cooperativas")

        coop.nombre      = request.POST.get("nombre", coop.nombre)
        coop.max_boletos = int(request.POST.get("max_boletos", coop.max_boletos))
        coop.estado      = request.POST.get("estado", coop.estado)
        coop.save()
        messages.success(request, f"Cooperativa '{coop.nombre}' actualizada.")
        return redirect("cooperativas")

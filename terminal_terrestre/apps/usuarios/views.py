"""apps/usuarios/views.py"""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from apps.usuarios.mixins import AdminOSupervisorMixin, SoloAdminMixin
from .models import Usuario


class UsuariosListView(AdminOSupervisorMixin, View):
    template_name = "usuarios/usuarios_lista.html"

    def get(self, request):
        return render(request, self.template_name, {
            "usuarios": Usuario.objects.all().order_by("username")
        })


class UsuarioCreateView(SoloAdminMixin, View):
    def post(self, request):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Usuario y contraseña son obligatorios.")
            return redirect("usuarios")

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, f"El usuario '{username}' ya existe.")
            return redirect("usuarios")

        user = Usuario.objects.create(
            username=username,
            first_name=request.POST.get("first_name", ""),
            last_name=request.POST.get("last_name", ""),
            email=request.POST.get("email", ""),
            rol=request.POST.get("rol", "operador"),
            telefono=request.POST.get("telefono", ""),
            activo=True,
        )
        user.set_password(password)
        user.save()
        messages.success(request, f"Usuario '{username}' creado correctamente.")
        return redirect("usuarios")


class UsuarioEditView(SoloAdminMixin, View):
    def post(self, request, pk):
        try:
            user = Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
            return redirect("usuarios")

        user.username   = request.POST.get("username", user.username)
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name  = request.POST.get("last_name", user.last_name)
        user.email      = request.POST.get("email", user.email)
        user.rol        = request.POST.get("rol", user.rol)
        user.activo     = request.POST.get("activo", "true") == "true"

        new_pw = request.POST.get("password", "").strip()
        if new_pw:
            user.set_password(new_pw)

        user.save()
        messages.success(request, f"Usuario '{user.username}' actualizado.")
        return redirect("usuarios")


class UsuarioDeleteView(SoloAdminMixin, View):
    def post(self, request, pk):
        if str(pk) == str(request.user.pk):
            messages.error(request, "No puedes eliminar tu propia cuenta.")
            return redirect("usuarios")
        try:
            user = Usuario.objects.get(pk=pk)
            nombre = user.username
            user.delete()
            messages.success(request, f"Usuario '{nombre}' eliminado.")
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
        return redirect("usuarios")

"""
apps/usuarios/views_auth.py
============================
Login/logout con sesiones Django (sin JWT para el frontend HTML).
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views import View


class LoginView(View):
    template_name = "login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("qr_generar")
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            return render(request, self.template_name, {
                "error": "Por favor ingresa tu usuario y contraseña.",
                "username": username,
            })

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, self.template_name, {
                "error": "Credenciales incorrectas. Verifica tu usuario y contraseña.",
                "username": username,
            })

        if not user.activo:
            return render(request, self.template_name, {
                "error": "Tu cuenta está desactivada. Contacta al administrador.",
                "username": username,
            })

        login(request, user)
        messages.success(request, f"Bienvenido, {user.get_full_name() or user.username}.")
        return redirect(request.GET.get("next", "qr_generar"))


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("login")

    def post(self, request):
        logout(request)
        return redirect("login")

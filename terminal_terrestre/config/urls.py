"""
Terminal Terrestre — URLs principales (Django Template Views)
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.usuarios.views_auth import LoginView, LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/",  LoginView.as_view(),  name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", RedirectView.as_view(pattern_name="qr_generar", permanent=False)),
    path("qr/",            include("apps.qr_codes.urls")),
    path("dashboard/",     include("apps.dashboard.urls")),
    path("recaudaciones/", include("apps.dashboard.recaudacion_urls")),
    path("tickets/",       include("apps.tickets.urls")),
    path("cooperativas/",  include("apps.cooperativas.urls")),
    path("usuarios/",      include("apps.usuarios.urls.usuario_urls")),
    # Endpoint API público (torniquetes externos)
    path("api/accesos/",   include("apps.accesos.api_urls")),
]

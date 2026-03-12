"""apps/usuarios/urls/usuario_urls.py"""
from django.urls import path
from apps.usuarios.views import (
    UsuariosListView, UsuarioCreateView, UsuarioEditView, UsuarioDeleteView
)

urlpatterns = [
    path("",                  UsuariosListView.as_view(),  name="usuarios"),
    path("crear/",            UsuarioCreateView.as_view(), name="usuario_create"),
    path("<int:pk>/editar/",  UsuarioEditView.as_view(),   name="usuario_edit"),
    path("<int:pk>/eliminar/",UsuarioDeleteView.as_view(), name="usuario_delete"),
]

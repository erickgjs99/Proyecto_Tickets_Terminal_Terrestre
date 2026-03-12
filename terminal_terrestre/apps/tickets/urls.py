"""apps/tickets/urls.py"""
from django.urls import path
from .views import TiposTicketListView, TipoTicketCreateView, TipoTicketEditView, TipoTicketDeleteView

urlpatterns = [
    path("tipos/",               TiposTicketListView.as_view(),  name="tipos_ticket"),
    path("tipos/crear/",         TipoTicketCreateView.as_view(), name="tipo_ticket_create"),
    path("tipos/<int:pk>/editar/",TipoTicketEditView.as_view(),  name="tipo_ticket_edit"),
    path("tipos/<int:pk>/eliminar/",TipoTicketDeleteView.as_view(), name="tipo_ticket_delete"),
]

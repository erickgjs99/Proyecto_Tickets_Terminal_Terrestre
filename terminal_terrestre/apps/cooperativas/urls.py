"""apps/cooperativas/urls.py"""
from django.urls import path
from .views import CooperativasListView, CooperativaCreateView, CooperativaEditView

urlpatterns = [
    path("",              CooperativasListView.as_view(), name="cooperativas"),
    path("crear/",        CooperativaCreateView.as_view(), name="cooperativa_create"),
    path("<int:pk>/editar/", CooperativaEditView.as_view(), name="cooperativa_edit"),
]

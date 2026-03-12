"""
apps/dashboard/views.py
========================
Vistas del dashboard con estadísticas del día.
"""

import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.db.models.functions import TruncHour
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.qr_codes.models import EstadoTicket, TicketQR
from apps.ventas.models import Venta


class DashboardView(LoginRequiredMixin, View):
    template_name = "dashboard/dashboard.html"

    def get(self, request):
        hoy = timezone.now().date()

        ventas_hoy  = Venta.objects.filter(fecha__date=hoy)
        tickets_hoy = TicketQR.objects.filter(fecha_creacion__date=hoy)

        ingresos_hoy = ventas_hoy.aggregate(t=Sum("precio"))["t"] or Decimal("0")

        resumen = {
            "ingresos_hoy":     float(ingresos_hoy),
            "tickets_generados": tickets_hoy.count(),
            "tickets_activos":   tickets_hoy.filter(estado=EstadoTicket.ACTIVO).count(),
            "tickets_usados":    tickets_hoy.filter(estado=EstadoTicket.USADO).count(),
            "tickets_expirados": tickets_hoy.filter(estado=EstadoTicket.EXPIRADO).count(),
        }

        # Alertas
        ahora = timezone.now()
        alertas = {
            "tickets_por_expirar": TicketQR.objects.filter(
                estado=EstadoTicket.ACTIVO,
                fecha_expiracion__lte=ahora + timedelta(minutes=5),
            ).count(),
            "tickets_con_error_hoy": tickets_hoy.filter(estado=EstadoTicket.ERROR).count(),
        }

        # Ventas por tipo
        vt_qs = (
            ventas_hoy.values("tipo_ticket__nombre", "tipo_ticket__precio")
            .annotate(cantidad=Count("id"), total=Sum("precio"))
            .order_by("-total")
        )
        ventas_por_tipo = [
            {
                "tipo": item["tipo_ticket__nombre"],
                "precio_unitario": float(item["tipo_ticket__precio"]),
                "cantidad": item["cantidad"],
                "total": float(item["total"] or 0),
            }
            for item in vt_qs
        ]

        # Ventas por hora
        vh_qs = (
            ventas_hoy.annotate(hora=TruncHour("fecha"))
            .values("hora").annotate(cantidad=Count("id"), total=Sum("precio"))
            .order_by("hora")
        )
        ventas_por_hora = [
            {"hora": item["hora"].strftime("%H:00"), "cantidad": item["cantidad"]}
            for item in vh_qs
        ]

        # Ingresos 30 días
        hace_30 = hoy - timedelta(days=30)
        id_qs = (
            Venta.objects.filter(fecha__date__gte=hace_30)
            .values("fecha__date").annotate(total=Sum("precio"), cantidad=Count("id"))
            .order_by("fecha__date")
        )
        ingresos_diarios = [
            {"fecha": item["fecha__date"].strftime("%d/%m"), "total": float(item["total"] or 0)}
            for item in id_qs
        ]

        ctx = {
            "resumen": resumen,
            "alertas": alertas,
            "ventas_por_tipo": ventas_por_tipo,
            "ventas_por_hora": ventas_por_hora,
            "ingresos_diarios": ingresos_diarios,
            # Datos serializados para Chart.js (JSON seguro)
            "ventas_tipo_labels":   json.dumps([v["tipo"] for v in ventas_por_tipo]),
            "ventas_tipo_totales":  json.dumps([v["total"] for v in ventas_por_tipo]),
            "ventas_hora_labels":   json.dumps([v["hora"] for v in ventas_por_hora]),
            "ventas_hora_cant":     json.dumps([v["cantidad"] for v in ventas_por_hora]),
            "ingresos_labels":      json.dumps([v["fecha"] for v in ingresos_diarios]),
            "ingresos_totales":     json.dumps([v["total"] for v in ingresos_diarios]),
        }
        return render(request, self.template_name, ctx)

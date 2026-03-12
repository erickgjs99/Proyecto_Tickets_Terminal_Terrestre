"""
apps/dashboard/recaudacion_views.py
=====================================
Vista del reporte oficial de recaudaciones diarias/mensuales/anuales.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.shortcuts import render
from django.views import View
from num2words import num2words

from apps.usuarios.models import Usuario
from apps.ventas.models import Venta


def _total_en_letras(total: Decimal) -> str:
    """Convierte monto a texto en español para el reporte oficial."""
    try:
        entero   = int(total)
        centavos = int(round((total - entero) * 100))
        letras   = num2words(entero, lang="es").upper()
        if centavos:
            return f"{letras} DÓLARES CON {centavos:02d}/100 CENTAVOS"
        return f"{letras} DÓLARES EXACTOS"
    except Exception:
        return str(total)


class RecaudacionesView(LoginRequiredMixin, View):
    template_name = "recaudaciones/recaudaciones.html"

    def get(self, request):
        user       = request.user
        es_supervisor_o_admin = user.es_supervisor or user.es_admin

        modo       = request.GET.get("modo", "diario")
        fecha_str  = request.GET.get("fecha", "")
        mes_str    = request.GET.get("mes", "")
        anio_str   = request.GET.get("anio", "")

        # Operadores solo pueden ver sus propios reportes; ignoran el filtro de operador del GET
        if es_supervisor_o_admin:
            operador_id = request.GET.get("operador", "")
        else:
            operador_id = str(user.id)

        hoy        = date.today()
        mes_actual = hoy.strftime("%Y-%m")
        anio_actual= str(hoy.year)

        ctx = {
            "modo": modo,
            "es_supervisor_o_admin": es_supervisor_o_admin,
            "filtros": {
                "fecha": fecha_str, "mes": mes_str,
                "anio": anio_str, "operador": operador_id,
            },
            "hoy": hoy.strftime("%Y-%m-%d"),
            "mes_actual": mes_actual,
            "anio_actual": anio_actual,
            # Solo supervisor/admin ven el selector de operador
            "operadores": Usuario.objects.filter(is_active=True).order_by("first_name") if es_supervisor_o_admin else [],
        }

        # Solo generar si hay algún parámetro de búsqueda
        if any([fecha_str, mes_str, anio_str]) or request.GET.get("_submit"):
            ctx["reporte"] = self._calcular_reporte(
                modo, fecha_str, mes_str, anio_str, operador_id
            )

        return render(request, self.template_name, ctx)

    def _calcular_reporte(self, modo, fecha_str, mes_str, anio_str, operador_id):
        qs = Venta.objects.select_related("tipo_ticket", "operador").order_by("numero_ticket")

        if modo == "diario" and fecha_str:
            qs = qs.filter(fecha__date=fecha_str)
            periodo = fecha_str
        elif modo == "mensual" and mes_str:
            anio, mes = mes_str.split("-")
            qs = qs.filter(fecha__year=anio, fecha__month=mes)
            periodo = mes_str
        elif modo == "anual" and anio_str:
            qs = qs.filter(fecha__year=anio_str)
            periodo = anio_str
        else:
            qs = qs.filter(fecha__date=date.today())
            periodo = date.today().strftime("%Y-%m-%d")

        if operador_id:
            qs = qs.filter(operador_id=operador_id)

        if not qs.exists():
            return {
                "periodo": periodo, "filas": [],
                "total": 0, "total_letras": "CERO DÓLARES EXACTOS",
                "ticket_inicial": None, "ticket_final": None,
            }

        ticket_inicial = qs.order_by("numero_ticket").first().numero_ticket
        ticket_final   = qs.order_by("-numero_ticket").first().numero_ticket

        grupos = (
            qs.values("tipo_ticket__nombre", "tipo_ticket__precio")
            .annotate(cantidad=Count("id"), total=Sum("precio"))
            .order_by("tipo_ticket__nombre")
        )

        filas = []
        for g in grupos:
            ventas_tipo = qs.filter(tipo_ticket__nombre=g["tipo_ticket__nombre"]).order_by("numero_ticket")
            filas.append({
                "detalle":        g["tipo_ticket__nombre"],
                "ticket_inicial": ventas_tipo.first().numero_ticket,
                "ticket_final":   ventas_tipo.last().numero_ticket,
                "cantidad":       g["cantidad"],
                "valor_unitario": float(g["tipo_ticket__precio"]),
                "valor_total":    float(g["total"] or 0),
            })

        total = sum(f["valor_total"] for f in filas)

        return {
            "periodo": periodo,
            "ticket_inicial": ticket_inicial,
            "ticket_final": ticket_final,
            "filas": filas,
            "total": total,
            "total_letras": _total_en_letras(Decimal(str(total))),
        }

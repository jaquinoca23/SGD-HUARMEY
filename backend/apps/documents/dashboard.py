"""Resumen de la pantalla de inicio según el nivel de acceso.

Solo se informan cifras REALES. Los contadores que dependen del flujo documental (despacho,
bandejas, envíos), que se implementa en la Fase 2, se devuelven con `available: false` y
`value: null`: la interfaz muestra «—» en lugar de un cero que parezca un dato.
"""
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organization.models import Assignment
from apps.organization.services import access_level_for, primary_assignment

from .models import DocumentDraft
from .services import visible_drafts


def _item(key, label, description, value=None, *, indent=False, link=None):
    return {
        "key": key,
        "label": label,
        "description": description,
        "value": value,
        "available": value is not None,
        "indent": indent,
        "link": link,
    }


class DashboardSummaryView(APIView):
    """Contadores del inicio: personal (propios) o total (toda la oficina)."""

    def get(self, request):
        user = request.user
        assignment = primary_assignment(user)
        level = access_level_for(user)
        drafts = visible_drafts(user).filter(status=DocumentDraft.Status.DRAFT)

        if level == Assignment.AccessLevel.TOTAL and assignment:
            drafts_value = drafts.filter(office=assignment.office).count()
            items = [
                _item("para_firma", "Para firma", "Documentos administrativos listos para la firma"),
                _item("borradores", "Borradores", "Documentos administrativos en proceso de elaboración",
                      drafts_value, link="/nuevo-documento"),
                _item("bandeja_entrada", "Bandeja de entrada", "Documentos recibidos"),
                _item("delegados", "Delegados", "Documentos recibidos", indent=True),
                _item("enviados", "Enviados", "Documentos administrativos derivados"),
            ]
            title = f"Documentos de {assignment.office.code}"
        else:
            own = drafts.filter(Q(author=user) | Q(assigned_to=user)).count()
            items = [
                _item("para_despacho", "Para despacho", "Documentos administrativos listos para la firma"),
                _item("en_proyecto", "En proyecto", "Documentos administrativos en proceso de elaboración",
                      own, link="/nuevo-documento"),
                _item("no_leidos", "No leídos", "Documentos pendientes de recibir"),
                _item("recibidos", "Recibidos", "Documentos recibidos"),
            ]
            title = f"Documentos de {assignment.office.code}" if assignment else "Mis documentos"

        return Response({
            "access_level": level,
            "title": title,
            "subtitle": "Resumen de los documentos principales",
            "office": ({"id": assignment.office_id, "code": assignment.office.code, "name": assignment.office.name}
                       if assignment else None),
            "items": items,
        })

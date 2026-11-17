"""Reglas de visibilidad y resolución de plantilla para borradores.

Visibilidad (NO concede permisos de firma, aprobación, emisión ni anulación):
  - Acceso personal: documentos que el usuario generó o que tiene asignados.
  - Acceso total: además, los documentos de su oficina, salvo los confidenciales
    (esos solo los ven su autor y la persona asignada).
"""
from django.db.models import Q

from apps.organization.services import total_access_office_ids
from apps.templates.models import Template

from .models import DocumentDraft


def visible_drafts(user):
    qs = DocumentDraft.objects.select_related(
        "document_type", "office", "author", "assigned_to", "template_version", "template_version__template"
    )
    if not user or not user.is_authenticated or not user.is_active:
        return qs.none()
    condition = Q(author=user) | Q(assigned_to=user)
    offices = total_access_office_ids(user)
    if offices:
        condition |= Q(office_id__in=offices) & ~Q(confidentiality=DocumentDraft.Confidentiality.CONFIDENTIAL)
    return qs.filter(condition)


def resolve_template_version(document_type, office):
    """Versión vigente de la plantilla aplicable: 1) propia de la oficina, 2) predeterminada del
    tipo, 3) general del tipo. Devuelve None si no hay plantilla con versión vigente."""
    base = Template.objects.filter(
        document_type=document_type, is_active=True, current_version__isnull=False
    ).select_related("current_version")

    own = base.filter(office=office).first()
    if own:
        return own.current_version

    default = document_type.default_template
    if (default and default.is_active and default.current_version_id
            and (default.office_id is None or default.office_id == office.id)):
        return default.current_version

    general = base.filter(office__isnull=True).first()
    return general.current_version if general else None

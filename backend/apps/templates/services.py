import hashlib

from django.db import transaction
from django.db.models import Max, Q

from apps.organization.services import user_office_ids
from apps.permissions.services import user_has_permission

from .models import Template, TemplateVersion


def visible_templates(user):
    """Plantillas que el usuario puede ver. Las privadas solo son visibles para la oficina
    indicada; quien gestiona plantillas ve todas."""
    qs = Template.objects.select_related("document_type", "office", "current_version", "created_by")
    if user_has_permission(user, "templates.manage"):
        return qs
    return qs.filter(is_active=True).filter(Q(is_private=False) | Q(office_id__in=user_office_ids(user)))


def user_can_access_template(user, template) -> bool:
    if user_has_permission(user, "templates.manage"):
        return True
    if not template.is_active:
        return False
    return (not template.is_private) or template.office_id in user_office_ids(user)


@transaction.atomic
def add_version(template, uploaded, *, user, version_label="", notes="", is_official=False, set_current=True):
    """Crea una nueva versión (número correlativo) y, opcionalmente, la deja como vigente."""
    # Bloquea la plantilla para numerar de forma segura ante cargas simultáneas.
    Template.objects.select_for_update().get(pk=template.pk)
    last = template.versions.aggregate(m=Max("version_number"))["m"] or 0
    digest = hashlib.sha256()
    for chunk in uploaded.chunks():
        digest.update(chunk)
    uploaded.seek(0)
    version = TemplateVersion(
        template=template,
        version_number=last + 1,
        version_label=version_label,
        original_filename=uploaded.name[:255],
        file_size=uploaded.size,
        checksum_sha256=digest.hexdigest(),
        is_official=is_official,
        notes=notes,
        created_by=user,
    )
    version.file.save(uploaded.name, uploaded, save=False)
    version.save()
    if set_current or template.current_version_id is None:
        template.current_version = version
        template.save(update_fields=["current_version", "updated_at"])
    return version

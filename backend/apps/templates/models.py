import os
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.common.models import TimeStampedModel
from apps.common.storage import PrivateFileStorage


class Template(TimeStampedModel):
    """Plantilla documental. Su `current_version` es la versión vigente.

    Solo puede haber una plantilla ACTIVA por (tipo documental, oficina) y una general
    (sin oficina) por tipo: así la versión vigente de cada ámbito es inequívoca.
    """

    document_type = models.ForeignKey("document_types.DocumentType", on_delete=models.PROTECT, related_name="templates")
    name = models.CharField("nombre", max_length=200)
    description = models.CharField("descripción", max_length=300, blank=True)
    office = models.ForeignKey(
        "organization.Office", null=True, blank=True, on_delete=models.PROTECT, related_name="templates",
        verbose_name="oficina (vacío = general)",
    )
    is_private = models.BooleanField("privada (solo la oficina indicada)", default=False)
    is_active = models.BooleanField("activa", default=True)
    current_version = models.ForeignKey(
        "doc_templates.TemplateVersion", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name="versión vigente",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["document_type__name", "name"]
        verbose_name = "plantilla"
        verbose_name_plural = "plantillas"
        constraints = [
            models.CheckConstraint(
                condition=Q(is_private=False) | Q(office__isnull=False), name="private_template_requires_office"
            ),
            models.UniqueConstraint(
                fields=["document_type"], condition=Q(is_active=True, office__isnull=True),
                name="uniq_active_general_template_per_type",
            ),
            models.UniqueConstraint(
                fields=["document_type", "office"], condition=Q(is_active=True, office__isnull=False),
                name="uniq_active_office_template_per_type",
            ),
        ]

    def __str__(self):
        return self.name


def template_upload_path(instance, filename):
    return f"templates/{instance.template_id}/v{instance.version_number}-{uuid.uuid4().hex}.docx"


class TemplateVersion(models.Model):
    """Versión de una plantilla. Inmutable una vez creada (la API no ofrece edición)."""

    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField("número de versión")
    version_label = models.CharField("etiqueta de versión", max_length=50, blank=True)
    file = models.FileField(upload_to=template_upload_path, storage=PrivateFileStorage(), max_length=255)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    checksum_sha256 = models.CharField(max_length=64)
    is_official = models.BooleanField(
        "oficial", default=False, help_text="False = plantilla de demostración / no oficial."
    )
    notes = models.CharField("notas", max_length=500, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        verbose_name = "versión de plantilla"
        verbose_name_plural = "versiones de plantilla"
        constraints = [
            models.UniqueConstraint(fields=["template", "version_number"], name="uniq_template_version_number")
        ]

    @property
    def download_name(self):
        return os.path.basename(self.original_filename) or f"plantilla-v{self.version_number}.docx"

    def __str__(self):
        return f"{self.template_id} v{self.version_number}"

import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class DocumentDraft(TimeStampedModel):
    """Registro inicial de un borrador. El contenido (archivo DOCX) vivirá principalmente en el
    equipo del usuario, gestionado por SGDGuarmail (fase posterior). Aquí solo se guardan
    metadatos, el vínculo con la versión de plantilla usada y los campos de bloqueo previstos.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"

    class Confidentiality(models.TextChoices):
        NORMAL = "NORMAL", "Normal"
        CONFIDENTIAL = "CONFIDENTIAL", "Confidencial"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField("asunto / título", max_length=250)
    document_type = models.ForeignKey("document_types.DocumentType", on_delete=models.PROTECT, related_name="drafts")
    template_version = models.ForeignKey(
        "doc_templates.TemplateVersion", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    office = models.ForeignKey("organization.Office", on_delete=models.PROTECT, related_name="drafts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="authored_drafts")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_drafts"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    confidentiality = models.CharField(max_length=14, choices=Confidentiality.choices, default=Confidentiality.NORMAL)

    # Previsto para el bloqueo de edición única (fase 2, SGDGuarmail). No se usa todavía.
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    lock_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "borrador"
        verbose_name_plural = "borradores"
        indexes = [models.Index(fields=["office", "status"]), models.Index(fields=["author"])]

    def __str__(self):
        return self.title

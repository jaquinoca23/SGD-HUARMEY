from django.db import models

from apps.common.models import TimeStampedModel


class DocumentType(TimeStampedModel):
    class IssuanceScope(models.TextChoices):
        OFFICE = "OFFICE", "Dentro de la misma oficina"
        INTERNAL = "INTERNAL", "Entre oficinas de la municipalidad"
        EXTERNAL = "EXTERNAL", "Hacia el exterior"
        NORMATIVE = "NORMATIVE", "Normativo / órgano de gobierno"

    code = models.CharField("código", max_length=40, unique=True)
    name = models.CharField("nombre", max_length=150, unique=True)
    description = models.CharField("descripción", max_length=300, blank=True)
    requires_signature = models.BooleanField("requiere firma", default=True)
    issuance_scope = models.CharField("ámbito de emisión", max_length=10, choices=IssuanceScope.choices,
                                      default=IssuanceScope.INTERNAL)
    allows_multiple_recipients = models.BooleanField("permite destinatarios múltiples", default=False)
    default_template = models.ForeignKey(
        "doc_templates.Template", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name="plantilla predeterminada",
    )
    is_active = models.BooleanField("activo", default=True)
    sort_order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "tipo documental"
        verbose_name_plural = "tipos documentales"

    def __str__(self):
        return self.name

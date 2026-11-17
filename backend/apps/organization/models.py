from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.common.models import TimeStampedModel


class Office(TimeStampedModel):
    """Oficina, gerencia, subgerencia u órgano. Jerarquía mediante `parent`."""

    class Kind(models.TextChoices):
        GOVERNING = "GOVERNING", "Órgano de gobierno y dirección"
        GENERAL = "GENERAL", "Oficina general"
        MANAGEMENT = "MANAGEMENT", "Gerencia"
        UNIT = "UNIT", "Subgerencia / unidad"
        OTHER = "OTHER", "Otro órgano"

    code = models.CharField("código", max_length=30, unique=True)
    name = models.CharField("nombre", max_length=200)
    kind = models.CharField("tipo", max_length=12, choices=Kind.choices, default=Kind.UNIT)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children",
        verbose_name="depende de",
    )
    is_active = models.BooleanField("activa", default=True)
    sort_order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "oficina"
        verbose_name_plural = "oficinas"
        constraints = [
            models.CheckConstraint(condition=~Q(parent=F("id")), name="office_not_own_parent"),
        ]
        indexes = [models.Index(fields=["parent", "name"])]

    def __str__(self):
        return self.name


class Position(TimeStampedModel):
    """Cargo. `is_head` marca cargos de jefatura (base para competencias de firma futuras)."""

    code = models.CharField("código", max_length=40, unique=True)
    name = models.CharField("nombre", max_length=150)
    is_head = models.BooleanField("cargo de jefatura", default=False)
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "cargo"
        verbose_name_plural = "cargos"

    def __str__(self):
        return self.name


class Assignment(TimeStampedModel):
    """Pertenencia de un usuario a una oficina con un cargo y un NIVEL DE VISIBILIDAD.

    El nivel de acceso (PERSONAL/TOTAL) solo define qué documentos se ven. No otorga
    permisos operativos ni competencia de firma (ver app permissions).
    """

    class AccessLevel(models.TextChoices):
        PERSONAL = "PERSONAL", "Acceso personal"
        TOTAL = "TOTAL", "Acceso total de la oficina"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments")
    office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name="assignments")
    position = models.ForeignKey(Position, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    access_level = models.CharField(max_length=10, choices=AccessLevel.choices, default=AccessLevel.PERSONAL)
    is_primary = models.BooleanField("oficina principal", default=False)
    is_acting = models.BooleanField("encargatura", default=False)
    is_active = models.BooleanField("vigente", default=True)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-is_primary", "office__name"]
        verbose_name = "asignación"
        verbose_name_plural = "asignaciones"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "office"], condition=Q(is_active=True), name="uniq_active_assignment_user_office"
            ),
            models.UniqueConstraint(
                fields=["user"], condition=Q(is_primary=True, is_active=True), name="uniq_primary_assignment_per_user"
            ),
            models.CheckConstraint(
                condition=Q(ends_on__isnull=True) | Q(starts_on__isnull=True) | Q(ends_on__gte=F("starts_on")),
                name="assignment_dates_valid",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} → {self.office_id} ({self.access_level})"

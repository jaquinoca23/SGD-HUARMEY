from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.common.models import TimeStampedModel


class AppPermission(models.Model):
    """Permiso del sistema identificado por código (p. ej. 'offices.manage')."""

    class Category(models.TextChoices):
        ADMINISTRATION = "ADMINISTRATION", "Administración"
        OPERATIONAL = "OPERATIONAL", "Operativo"
        SIGNATURE = "SIGNATURE", "Firma y emisión (reservado para fases posteriores)"

    code = models.CharField(max_length=60, unique=True)
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=300, blank=True)
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.OPERATIONAL)
    direct_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="UserPermission", through_fields=("permission", "user"),
        related_name="extra_permissions", blank=True,
    )

    class Meta:
        ordering = ["category", "code"]
        verbose_name = "permiso"
        verbose_name_plural = "permisos"

    def __str__(self):
        return self.code


class Role(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True)
    permissions = models.ManyToManyField(AppPermission, related_name="roles", blank=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="UserRole", through_fields=("role", "user"),
        related_name="roles", blank=True,
    )
    is_system = models.BooleanField("rol del sistema", default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "rol"
        verbose_name_plural = "roles"

    def __str__(self):
        return self.name


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role")]


class UserPermission(models.Model):
    """Permiso concedido directamente a un usuario (además de sus roles)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    permission = models.ForeignKey(AppPermission, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "permission"], name="uniq_user_permission")]


class SigningAuthority(TimeStampedModel):
    """Competencia de firma de un usuario para una oficina (y opcionalmente un tipo documental).

    Es independiente del nivel de acceso y de los roles: tener acceso total NO implica firmar.
    En la Fase 01 solo se registra; el flujo de firma se implementa en fases posteriores y
    NO constituye firma digital con validez jurídica.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="signing_authorities")
    office = models.ForeignKey("organization.Office", on_delete=models.PROTECT, related_name="+")
    document_type = models.ForeignKey(
        "document_types.DocumentType", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
        help_text="Vacío = todos los tipos que requieran firma.",
    )
    basis = models.CharField("sustento (resolución de designación o encargatura)", max_length=300, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["office__name", "user__last_name"]
        verbose_name = "competencia de firma"
        verbose_name_plural = "competencias de firma"
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_from__isnull=True) | Q(valid_until__gte=F("valid_from")),
                name="signing_authority_dates_valid",
            )
        ]

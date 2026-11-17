from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Registro de solo adición: no se modifica ni se elimina desde la aplicación."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    actor_username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=40, db_index=True)
    entity_type = models.CharField(max_length=80, db_index=True)
    entity_id = models.CharField(max_length=64, blank=True)
    entity_repr = models.CharField(max_length=255, blank=True)
    office = models.ForeignKey(
        "organization.Office", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionError("Los registros de auditoría son inmutables.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Los registros de auditoría no se pueden eliminar.")

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.actor_username} {self.action} {self.entity_type}"

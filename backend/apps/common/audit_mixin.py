"""ViewSet base que registra en auditoría las altas, cambios y desactivaciones.

DELETE no borra filas: desactiva el registro (is_active=False) para conservar trazabilidad.
"""
from django.db import transaction
from rest_framework import viewsets

from apps.audit.services import log_action, snapshot


class AuditedModelViewSet(viewsets.ModelViewSet):
    def get_audit_office(self, instance):
        """Oficina asociada a la acción (opcional)."""
        return None

    def get_audit_extra(self, instance) -> dict:
        """Datos adicionales (p. ej. relaciones M2M) que forman parte de la instantánea."""
        return {}

    def _snap(self, instance):
        data = snapshot(instance)
        data.update(self.get_audit_extra(instance))
        return data

    def before_deactivate(self, instance):
        """Gancho para impedir desactivaciones (lanzar ValidationError)."""

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            log_action(
                self.request,
                "CREATE",
                instance,
                changes={"despues": self._snap(instance)},
                office=self.get_audit_office(instance),
            )

    def perform_update(self, serializer):
        before = self._snap(serializer.instance)
        with transaction.atomic():
            instance = serializer.save()
            after = self._snap(instance)
            diff = {
                key: {"antes": before.get(key), "despues": value}
                for key, value in after.items()
                if before.get(key) != value
            }
            if diff:
                log_action(
                    self.request,
                    "UPDATE",
                    instance,
                    changes=diff,
                    office=self.get_audit_office(instance),
                )

    def perform_destroy(self, instance):
        self.before_deactivate(instance)
        with transaction.atomic():
            instance.is_active = False
            instance.save(update_fields=["is_active", "updated_at"])
            log_action(
                self.request,
                "DEACTIVATE",
                instance,
                office=self.get_audit_office(instance),
            )

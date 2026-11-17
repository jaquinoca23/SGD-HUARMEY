from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.common.permissions import ActionPermission

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Consulta de auditoría (solo lectura; requiere audit.view)."""

    queryset = AuditLog.objects.select_related("office")
    serializer_class = AuditLogSerializer
    permission_classes = [ActionPermission]
    permission_map = {"list": "audit.view", "retrieve": "audit.view"}
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["actor_username", "action", "entity_type", "entity_repr"]
    ordering_fields = ["created_at", "action", "entity_type"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        for param, lookup in (("action", "action"), ("entity_type", "entity_type"), ("actor", "actor_id")):
            if params.get(param):
                qs = qs.filter(**{lookup: params[param]})
        return qs

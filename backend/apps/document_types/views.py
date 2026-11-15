from rest_framework.filters import OrderingFilter, SearchFilter

from apps.common.audit_mixin import AuditedModelViewSet
from apps.common.permissions import ANY_AUTHENTICATED, ActionPermission
from apps.permissions.services import user_has_permission

from .models import DocumentType
from .serializers import DocumentTypeSerializer


class DocumentTypeViewSet(AuditedModelViewSet):
    """Catálogo de tipos documentales. Lectura: cualquier usuario autenticado (solo activos,
    salvo quien gestiona el catálogo). Escritura: document_types.manage."""

    queryset = DocumentType.objects.select_related("default_template")
    serializer_class = DocumentTypeSerializer
    permission_classes = [ActionPermission]
    permission_map = {
        "list": ANY_AUTHENTICATED,
        "retrieve": ANY_AUTHENTICATED,
        "create": "document_types.manage",
        "update": "document_types.manage",
        "partial_update": "document_types.manage",
        "destroy": "document_types.manage",
    }
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code", "sort_order"]

    def get_queryset(self):
        qs = super().get_queryset()
        if not user_has_permission(self.request.user, "document_types.manage"):
            qs = qs.filter(is_active=True)
        return qs

from django.db.models import Count
from rest_framework import serializers, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.common.audit_mixin import AuditedModelViewSet
from apps.common.permissions import ActionPermission

from .models import AppPermission, Role, SigningAuthority
from .serializers import AppPermissionSerializer, RoleSerializer, SigningAuthoritySerializer

READ_CODES = ["users.view", "users.manage", "roles.manage"]


class AppPermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo de permisos (solo lectura; los permisos se definen en código)."""

    queryset = AppPermission.objects.all()
    serializer_class = AppPermissionSerializer
    permission_classes = [ActionPermission]
    permission_map = {"list": READ_CODES, "retrieve": READ_CODES}
    pagination_class = None


class RoleViewSet(AuditedModelViewSet):
    queryset = Role.objects.prefetch_related("permissions").annotate(users_count=Count("users", distinct=True))
    serializer_class = RoleSerializer
    permission_classes = [ActionPermission]
    permission_map = {
        "list": READ_CODES,
        "retrieve": READ_CODES,
        "create": "roles.manage",
        "update": "roles.manage",
        "partial_update": "roles.manage",
        "destroy": "roles.manage",
    }
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]

    def get_audit_extra(self, instance):
        return {"permissions": sorted(p.code for p in instance.permissions.all())}

    def before_deactivate(self, instance):
        if instance.is_system:
            raise serializers.ValidationError("Los roles del sistema no se pueden desactivar.")


class SigningAuthorityViewSet(AuditedModelViewSet):
    """Competencias de firma. Se registran aquí; el flujo de firma llega en fases posteriores."""

    queryset = SigningAuthority.objects.select_related("user", "office", "document_type")
    serializer_class = SigningAuthoritySerializer
    permission_classes = [ActionPermission]
    permission_map = {
        "list": ["users.view", "users.manage"],
        "retrieve": ["users.view", "users.manage"],
        "create": "users.manage",
        "update": "users.manage",
        "partial_update": "users.manage",
        "destroy": "users.manage",
    }
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["user__username", "user__last_name", "office__name"]

    def get_audit_office(self, instance):
        return instance.office

from django.db.models import Count
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.common.audit_mixin import AuditedModelViewSet
from apps.common.permissions import ANY_AUTHENTICATED, ActionPermission

from .models import Assignment, Office, Position
from .serializers import AssignmentSerializer, OfficeSerializer, PositionSerializer
from .services import office_tree


def _bool_param(value):
    if value is None or value == "":
        return None
    return str(value).lower() in {"1", "true", "yes", "si", "sí"}


class OfficeViewSet(AuditedModelViewSet):
    """Catálogo de oficinas. Lectura para cualquier usuario autenticado; escritura con offices.manage."""

    queryset = Office.objects.select_related("parent").annotate(children_count=Count("children"))
    serializer_class = OfficeSerializer
    permission_classes = [ActionPermission]
    permission_map = {
        "list": ANY_AUTHENTICATED,
        "retrieve": ANY_AUTHENTICATED,
        "tree": ANY_AUTHENTICATED,
        "create": "offices.manage",
        "update": "offices.manage",
        "partial_update": "offices.manage",
        "destroy": "offices.manage",
    }
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code", "sort_order", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("parent") == "null":
            qs = qs.filter(parent__isnull=True)
        elif params.get("parent"):
            qs = qs.filter(parent_id=params["parent"])
        if params.get("kind"):
            qs = qs.filter(kind=params["kind"])
        active = _bool_param(params.get("is_active"))
        if active is not None:
            qs = qs.filter(is_active=active)
        return qs

    def get_audit_office(self, instance):
        return instance

    @action(detail=False, methods=["get"], pagination_class=None)
    def tree(self, request):
        """Jerarquía completa de oficinas activas, sin paginación."""
        return Response(office_tree(Office.objects.filter(is_active=True).select_related("parent")))

    def before_deactivate(self, instance):
        if instance.children.filter(is_active=True).exists():
            raise serializers.ValidationError("Desactive primero las dependencias hijas activas.")
        if instance.assignments.filter(is_active=True).exists():
            raise serializers.ValidationError("La oficina tiene usuarios asignados vigentes.")


class PositionViewSet(AuditedModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [ActionPermission]
    permission_map = {
        "list": ANY_AUTHENTICATED,
        "retrieve": ANY_AUTHENTICATED,
        "create": "offices.manage",
        "update": "offices.manage",
        "partial_update": "offices.manage",
        "destroy": "offices.manage",
    }
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


class AssignmentViewSet(AuditedModelViewSet):
    """Asignaciones usuario-oficina-cargo-nivel de acceso. DELETE finaliza la asignación."""

    queryset = Assignment.objects.select_related("user", "office", "position")
    serializer_class = AssignmentSerializer
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
    search_fields = ["user__username", "user__first_name", "user__last_name", "office__name"]
    ordering_fields = ["created_at", "office__name"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("user"):
            qs = qs.filter(user_id=params["user"])
        if params.get("office"):
            qs = qs.filter(office_id=params["office"])
        active = _bool_param(params.get("is_active"))
        if active is not None:
            qs = qs.filter(is_active=active)
        return qs

    def get_audit_office(self, instance):
        return instance.office

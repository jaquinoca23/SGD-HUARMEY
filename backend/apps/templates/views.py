from django.db.models import Count
from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.audit.services import log_action
from apps.common.audit_mixin import AuditedModelViewSet
from apps.common.permissions import ANY_AUTHENTICATED, ActionPermission

from .models import TemplateVersion
from .serializers import (
    SetCurrentSerializer, TemplateSerializer, TemplateVersionSerializer, TemplateVersionUploadSerializer,
)
from .services import add_version, visible_templates
from .validators import DOCX_CONTENT_TYPE


class TemplateViewSet(AuditedModelViewSet):
    """Catálogo de plantillas. El acceso a las privadas se controla por objeto (oficina)."""

    serializer_class = TemplateSerializer
    permission_classes = [ActionPermission]
    permission_map = {
        "list": ANY_AUTHENTICATED,
        "retrieve": ANY_AUTHENTICATED,
        "versions:get": ANY_AUTHENTICATED,
        "create": "templates.manage",
        "update": "templates.manage",
        "partial_update": "templates.manage",
        "destroy": "templates.manage",
        "versions:post": "templates.manage",
        "set_current": "templates.manage",
    }
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "document_type__name", "office__name"]
    ordering_fields = ["name", "created_at", "updated_at"]

    def get_queryset(self):
        qs = visible_templates(self.request.user).annotate(versions_count=Count("versions"))
        params = self.request.query_params
        if params.get("document_type"):
            qs = qs.filter(document_type_id=params["document_type"])
        if params.get("office"):
            qs = qs.filter(office_id=params["office"])
        if params.get("is_active") in ("true", "false"):
            qs = qs.filter(is_active=params["is_active"] == "true")
        return qs

    def get_audit_office(self, instance):
        return instance.office

    def perform_create(self, serializer):
        serializer.validated_data["created_by"] = self.request.user
        super().perform_create(serializer)

    @action(detail=True, methods=["get", "post"], url_path="versions",
            parser_classes=[MultiPartParser, FormParser])
    def versions(self, request, pk=None):
        template = self.get_object()
        if request.method == "GET":
            qs = template.versions.select_related("template", "created_by")
            return Response(TemplateVersionSerializer(qs, many=True).data)

        serializer = TemplateVersionUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        version = add_version(
            template, data["file"], user=request.user, version_label=data["version_label"],
            notes=data["notes"], is_official=data["is_official"], set_current=data["set_current"],
        )
        log_action(
            request, "TEMPLATE_VERSION_CREATE", template, office=template.office,
            changes={"version": version.version_number, "sha256": version.checksum_sha256,
                     "is_official": version.is_official, "set_current": data["set_current"]},
        )
        return Response(TemplateVersionSerializer(version).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="set-current")
    def set_current(self, request, pk=None):
        """Define cuál versión es la vigente."""
        template = self.get_object()
        serializer = SetCurrentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = template.versions.filter(pk=serializer.validated_data["version_id"]).first()
        if version is None:
            return Response({"version_id": "La versión no pertenece a esta plantilla."},
                            status=status.HTTP_400_BAD_REQUEST)
        previous = template.current_version_id
        template.current_version = version
        template.save(update_fields=["current_version", "updated_at"])
        log_action(request, "TEMPLATE_SET_CURRENT", template, office=template.office,
                   changes={"antes": previous, "despues": version.pk})
        return Response(TemplateSerializer(self.get_queryset().get(pk=template.pk)).data)


class TemplateVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """Versiones de plantilla (solo lectura) y descarga controlada del DOCX."""

    serializer_class = TemplateVersionSerializer
    permission_classes = [ActionPermission]
    permission_map = {"list": ANY_AUTHENTICATED, "retrieve": ANY_AUTHENTICATED, "download": ANY_AUTHENTICATED}
    filter_backends = [OrderingFilter]
    ordering_fields = ["version_number", "created_at"]

    def get_queryset(self):
        visible = visible_templates(self.request.user).values("pk")
        qs = TemplateVersion.objects.filter(template__in=visible).select_related("template", "created_by")
        if self.request.query_params.get("template"):
            qs = qs.filter(template_id=self.request.query_params["template"])
        return qs

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        version = self.get_object()  # 404 si la plantilla no es visible para el usuario
        log_action(request, "TEMPLATE_DOWNLOAD", version.template, office=version.template.office,
                   changes={"version": version.version_number})
        response = FileResponse(version.file.open("rb"), as_attachment=True,
                                filename=version.download_name, content_type=DOCX_CONTENT_TYPE)
        response["X-Content-Type-Options"] = "nosniff"
        return response

from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.audit.services import log_action, snapshot
from apps.common.permissions import ANY_AUTHENTICATED, ActionPermission

from .serializers import DocumentDraftSerializer
from .services import visible_drafts


class DocumentDraftViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                           mixins.ListModelMixin, viewsets.GenericViewSet):
    """Registro inicial de borradores. Sin DELETE en esta fase.

    El queryset se limita por visibilidad (personal/total): un borrador ajeno responde 404.
    Editar (título/confidencialidad) solo lo puede hacer el autor.
    """

    serializer_class = DocumentDraftSerializer
    permission_classes = [ActionPermission]
    permission_map = {
        "list": ANY_AUTHENTICATED,
        "retrieve": ANY_AUTHENTICATED,
        "create": "documents.create",
        "update": "documents.create",
        "partial_update": "documents.create",
    }
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "document_type__name"]
    ordering_fields = ["created_at", "title"]

    def get_queryset(self):
        qs = visible_drafts(self.request.user)
        params = self.request.query_params
        if params.get("document_type"):
            qs = qs.filter(document_type_id=params["document_type"])
        if params.get("scope") == "mine":
            qs = qs.filter(author=self.request.user)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(self.request, "DRAFT_CREATE", instance, office=instance.office,
                   changes={"despues": snapshot(instance)})

    def perform_update(self, serializer):
        from rest_framework.exceptions import PermissionDenied

        if serializer.instance.author_id != self.request.user.id:
            raise PermissionDenied("Solo el autor puede modificar el borrador.")
        instance = serializer.save()
        log_action(self.request, "DRAFT_UPDATE", instance, office=instance.office)

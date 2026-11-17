"""Rutas de la API versionada (/api/v1/)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import UserViewSet
from apps.agent_integration.views import IntegrationStatusView
from apps.audit.views import AuditLogViewSet
from apps.document_types.views import DocumentTypeViewSet
from apps.documents.dashboard import DashboardSummaryView
from apps.documents.views import DocumentDraftViewSet
from apps.organization.views import AssignmentViewSet, OfficeViewSet, PositionViewSet
from apps.permissions.views import AppPermissionViewSet, RoleViewSet, SigningAuthorityViewSet
from apps.templates.views import TemplateVersionViewSet, TemplateViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("offices", OfficeViewSet, basename="office")
router.register("positions", PositionViewSet, basename="position")
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("permissions", AppPermissionViewSet, basename="permission")
router.register("roles", RoleViewSet, basename="role")
router.register("signing-authorities", SigningAuthorityViewSet, basename="signing-authority")
router.register("document-types", DocumentTypeViewSet, basename="document-type")
router.register("templates", TemplateViewSet, basename="template")
router.register("template-versions", TemplateVersionViewSet, basename="template-version")
router.register("drafts", DocumentDraftViewSet, basename="draft")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("integration/status/", IntegrationStatusView.as_view(), name="integration-status"),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("", include(router.urls)),
]

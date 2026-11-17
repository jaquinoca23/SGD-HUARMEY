import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.common.testing import client_for, docx_bytes, make_office, make_user, seed_permissions_and_roles
from apps.document_types.models import DocumentType
from apps.documents.models import DocumentDraft
from apps.documents.services import resolve_template_version, visible_drafts
from apps.templates.models import Template
from apps.templates.services import add_version

MEDIA = tempfile.mkdtemp(prefix="huarmy-test-docs-")


@override_settings(PRIVATE_MEDIA_ROOT=MEDIA)
class DraftVisibilityTests(APITestCase):
    """Acceso personal vs. acceso total (solo visibilidad)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.addClassCleanup(shutil.rmtree, MEDIA, ignore_errors=True)

    def setUp(self):
        seed_permissions_and_roles()
        self.ti = make_office("TI", "Tecnologías de la Información")
        self.rrhh = make_office("RRHH", "Gestión de Recursos Humanos")
        self.memo = DocumentType.objects.create(code="MEMORANDO", name="Memorando")
        self.personal = make_user("personal1", role="TRABAJADOR", office=self.ti, level="PERSONAL")
        self.total = make_user("total1", role="TRABAJADOR", office=self.ti, level="TOTAL")
        self.colleague = make_user("colega1", role="TRABAJADOR", office=self.ti, level="PERSONAL")
        self.other_office = make_user("otro1", role="TRABAJADOR", office=self.rrhh, level="TOTAL")

        self.own = self._draft("Propio", self.personal)
        self.colleague_draft = self._draft("De colega", self.colleague)
        self.assigned = self._draft("Asignado a personal", self.colleague, assigned_to=self.personal)
        self.confidential = self._draft("Confidencial", self.colleague, confidentiality="CONFIDENTIAL")
        self.rrhh_draft = self._draft("De otra oficina", self.other_office, office=self.rrhh)

    def _draft(self, title, author, office=None, **extra):
        return DocumentDraft.objects.create(
            title=title, document_type=self.memo, office=office or self.ti, author=author, **extra
        )

    def _titles(self, user):
        return sorted(d.title for d in visible_drafts(user))

    def test_personal_access_sees_only_own_and_assigned(self):
        self.assertEqual(self._titles(self.personal), ["Asignado a personal", "Propio"])

    def test_total_access_sees_whole_office_except_confidential(self):
        self.assertEqual(self._titles(self.total), ["Asignado a personal", "De colega", "Propio"])

    def test_total_access_never_crosses_offices(self):
        self.assertEqual(self._titles(self.other_office), ["De otra oficina"])

    def test_author_always_sees_own_confidential_draft(self):
        self.assertIn("Confidencial", self._titles(self.colleague))

    def test_api_list_and_detail_respect_visibility(self):
        client = client_for(self.personal)
        titles = sorted(d["title"] for d in client.get("/api/v1/drafts/").data["results"])
        self.assertEqual(titles, ["Asignado a personal", "Propio"])
        self.assertEqual(client.get(f"/api/v1/drafts/{self.colleague_draft.id}/").status_code, 404)
        self.assertEqual(client_for(self.total).get(f"/api/v1/drafts/{self.colleague_draft.id}/").status_code, 200)

    def test_only_author_can_edit_even_with_total_access(self):
        response = client_for(self.total).patch(
            f"/api/v1/drafts/{self.colleague_draft.id}/", {"title": "Cambiado"}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        ok = client_for(self.colleague).patch(
            f"/api/v1/drafts/{self.colleague_draft.id}/", {"title": "Cambiado"}, format="json"
        )
        self.assertEqual(ok.status_code, 200)


@override_settings(PRIVATE_MEDIA_ROOT=MEDIA)
class DraftCreationTests(APITestCase):
    def setUp(self):
        seed_permissions_and_roles()
        self.ti = make_office("TI", "Tecnologías de la Información")
        self.rrhh = make_office("RRHH", "Gestión de Recursos Humanos")
        self.memo = DocumentType.objects.create(code="MEMORANDO", name="Memorando")
        self.worker = make_user("worker1", role="TRABAJADOR", office=self.ti)
        self.mate = make_user("mate1", role="TRABAJADOR", office=self.ti)
        self.foreign = make_user("foreign1", role="TRABAJADOR", office=self.rrhh)

    def _add_template(self, office=None):
        template = Template.objects.create(document_type=self.memo, name=f"Plantilla {office or 'general'}", office=office)
        upload = SimpleUploadedFile("p.docx", docx_bytes())
        return add_version(template, upload, user=None, is_official=False)

    def test_creates_draft_in_primary_office_and_resolves_general_template(self):
        version = self._add_template()
        response = client_for(self.worker).post(
            "/api/v1/drafts/", {"document_type": self.memo.id, "title": "Solicitud de equipos"}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["office"], self.ti.id)
        self.assertEqual(response.data["author"], self.worker.id)
        self.assertEqual(response.data["status"], "DRAFT")
        self.assertTrue(response.data["template_resolved"])
        self.assertEqual(response.data["template_version"], version.id)

    def test_office_specific_template_wins_over_general(self):
        self._add_template()
        own = self._add_template(office=self.ti)
        response = client_for(self.worker).post(
            "/api/v1/drafts/", {"document_type": self.memo.id, "title": "X"}, format="json"
        )
        self.assertEqual(response.data["template_version"], own.id)

    def test_draft_without_template_is_still_created_but_flagged(self):
        response = client_for(self.worker).post(
            "/api/v1/drafts/", {"document_type": self.memo.id, "title": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data["template_resolved"])

    def test_can_assign_to_same_office_colleague_only(self):
        client = client_for(self.worker)
        ok = client.post("/api/v1/drafts/", {"document_type": self.memo.id, "title": "A", "assigned_to": self.mate.id}, format="json")
        self.assertEqual(ok.status_code, 201, ok.data)
        bad = client.post("/api/v1/drafts/", {"document_type": self.memo.id, "title": "B", "assigned_to": self.foreign.id}, format="json")
        self.assertEqual(bad.status_code, 400)

    def test_user_without_office_cannot_create(self):
        loner = make_user("loner1", role="TRABAJADOR")
        response = client_for(loner).post("/api/v1/drafts/", {"document_type": self.memo.id, "title": "X"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_cannot_create_in_foreign_office(self):
        response = client_for(self.worker).post(
            "/api/v1/drafts/", {"document_type": self.memo.id, "title": "X", "office": self.rrhh.id}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_user_without_documents_create_permission_is_forbidden(self):
        nobody = make_user("nobody1", office=self.ti)
        response = client_for(nobody).post("/api/v1/drafts/", {"document_type": self.memo.id, "title": "X"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_resolve_returns_none_without_templates(self):
        self.assertIsNone(resolve_template_version(self.memo, self.ti))

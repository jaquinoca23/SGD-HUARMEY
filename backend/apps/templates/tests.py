import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.common.testing import client_for, docx_bytes, make_office, make_user, seed_permissions_and_roles
from apps.document_types.models import DocumentType
from apps.templates.models import Template
from apps.templates.validators import DOCX_CONTENT_TYPE

MEDIA = tempfile.mkdtemp(prefix="huarmy-test-")


def docx_upload(name="plantilla.docx", text="Prueba"):
    return SimpleUploadedFile(name, docx_bytes(text), content_type=DOCX_CONTENT_TYPE)


@override_settings(PRIVATE_MEDIA_ROOT=MEDIA)
class TemplateAdministrationTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.addClassCleanup(shutil.rmtree, MEDIA, ignore_errors=True)

    def setUp(self):
        seed_permissions_and_roles()
        self.ti = make_office("TI", "Tecnologías de la Información")
        self.rrhh = make_office("RRHH", "Gestión de Recursos Humanos")
        self.secretaria = make_user("secretaria1", role="SECRETARIA_GENERAL", office=self.ti)
        self.worker_ti = make_user("worker.ti", role="TRABAJADOR", office=self.ti)
        self.worker_rrhh = make_user("worker.rrhh", role="TRABAJADOR", office=self.rrhh)
        self.memo = DocumentType.objects.create(code="MEMORANDO", name="Memorando")

    def _create_template(self, **extra):
        data = {"name": "Plantilla memorando", "document_type": self.memo.id}
        data.update(extra)
        return client_for(self.secretaria).post("/api/v1/templates/", data, format="json")

    def _upload(self, template_id, upload=None, **extra):
        data = {"file": upload or docx_upload(), **extra}
        return client_for(self.secretaria).post(f"/api/v1/templates/{template_id}/versions/", data, format="multipart")

    def test_manager_registers_template_and_uploads_docx_version(self):
        template = self._create_template()
        self.assertEqual(template.status_code, 201, template.data)
        version = self._upload(template.data["id"], is_official="false", version_label="1.0")
        self.assertEqual(version.status_code, 201, version.data)
        self.assertEqual(version.data["version_number"], 1)
        self.assertTrue(version.data["is_current"])
        self.assertFalse(version.data["is_official"])
        self.assertEqual(len(version.data["checksum_sha256"]), 64)

    def test_new_version_becomes_current_and_can_be_switched_back(self):
        template_id = self._create_template().data["id"]
        v1 = self._upload(template_id).data
        v2 = self._upload(template_id, docx_upload(text="Segunda")).data
        self.assertEqual(v2["version_number"], 2)
        self.assertEqual(Template.objects.get(pk=template_id).current_version_id, v2["id"])
        response = client_for(self.secretaria).post(
            f"/api/v1/templates/{template_id}/set-current/", {"version_id": v1["id"]}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(Template.objects.get(pk=template_id).current_version_id, v1["id"])

    def test_non_docx_extension_is_rejected(self):
        template_id = self._create_template().data["id"]
        bad = SimpleUploadedFile("malicioso.exe", b"MZ....", content_type="application/octet-stream")
        self.assertEqual(self._upload(template_id, bad).status_code, 400)

    def test_fake_docx_is_rejected(self):
        template_id = self._create_template().data["id"]
        fake = SimpleUploadedFile("falso.docx", b"esto no es un zip", content_type=DOCX_CONTENT_TYPE)
        self.assertEqual(self._upload(template_id, fake).status_code, 400)

    def test_oversized_file_is_rejected(self):
        template_id = self._create_template().data["id"]
        with override_settings(TEMPLATE_MAX_UPLOAD_MB=0):
            response = self._upload(template_id)
        self.assertEqual(response.status_code, 400)

    def test_worker_cannot_create_or_upload(self):
        response = client_for(self.worker_ti).post(
            "/api/v1/templates/", {"name": "X", "document_type": self.memo.id}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        template_id = self._create_template().data["id"]
        upload = client_for(self.worker_ti).post(
            f"/api/v1/templates/{template_id}/versions/", {"file": docx_upload()}, format="multipart"
        )
        self.assertEqual(upload.status_code, 403)

    def test_only_one_active_general_template_per_type(self):
        self.assertEqual(self._create_template().status_code, 201)
        self.assertEqual(self._create_template(name="Otra").status_code, 400)

    def test_private_template_requires_office(self):
        self.assertEqual(self._create_template(is_private=True).status_code, 400)

    def test_private_template_is_hidden_from_other_offices(self):
        created = self._create_template(office=self.ti.id, is_private=True)
        self.assertEqual(created.status_code, 201, created.data)
        template_id = created.data["id"]
        version_id = self._upload(template_id).data["id"]

        own = client_for(self.worker_ti)
        other = client_for(self.worker_rrhh)
        self.assertEqual(own.get(f"/api/v1/templates/{template_id}/").status_code, 200)
        self.assertEqual(other.get(f"/api/v1/templates/{template_id}/").status_code, 404)
        self.assertEqual(other.get("/api/v1/templates/").data["count"], 0)
        # La descarga del archivo también está protegida por objeto.
        self.assertEqual(own.get(f"/api/v1/template-versions/{version_id}/download/").status_code, 200)
        self.assertEqual(other.get(f"/api/v1/template-versions/{version_id}/download/").status_code, 404)

    def test_download_returns_the_docx(self):
        template_id = self._create_template().data["id"]
        version_id = self._upload(template_id).data["id"]
        response = client_for(self.worker_ti).get(f"/api/v1/template-versions/{version_id}/download/")
        self.assertEqual(response.status_code, 200)
        body = b"".join(response.streaming_content)
        self.assertTrue(body.startswith(b"PK"))
        self.assertIn("attachment", response["Content-Disposition"])

from rest_framework.test import APIClient, APITestCase

from apps.common.testing import client_for, make_office, make_user, seed_permissions_and_roles
from apps.document_types.models import DocumentType


class DocumentTypeTests(APITestCase):
    def setUp(self):
        seed_permissions_and_roles()
        office = make_office("TRAM", "Trámite Documentario")
        self.secretaria = make_user("secretaria1", role="SECRETARIA_GENERAL", office=office)
        self.worker = make_user("worker1", role="TRABAJADOR", office=office)
        DocumentType.objects.create(code="MEMORANDO", name="Memorando", requires_signature=True)
        DocumentType.objects.create(code="OLD", name="Tipo antiguo", is_active=False)

    def test_authenticated_user_sees_only_active_types(self):
        response = client_for(self.worker).get("/api/v1/document-types/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([t["code"] for t in response.data["results"]], ["MEMORANDO"])

    def test_catalog_manager_sees_inactive_types_too(self):
        response = client_for(self.secretaria).get("/api/v1/document-types/")
        self.assertEqual(response.data["count"], 2)

    def test_anonymous_gets_401(self):
        self.assertEqual(APIClient().get("/api/v1/document-types/").status_code, 401)

    def test_manager_registers_type_with_configuration(self):
        response = client_for(self.secretaria).post(
            "/api/v1/document-types/",
            {"code": "oficio multiple", "name": "Oficio múltiple", "requires_signature": True,
             "issuance_scope": "EXTERNAL", "allows_multiple_recipients": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["code"], "OFICIO_MULTIPLE")
        self.assertTrue(response.data["allows_multiple_recipients"])
        self.assertEqual(response.data["issuance_scope"], "EXTERNAL")

    def test_worker_cannot_create_type(self):
        response = client_for(self.worker).post("/api/v1/document-types/", {"code": "X", "name": "X"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_duplicate_name_rejected(self):
        response = client_for(self.secretaria).post(
            "/api/v1/document-types/", {"code": "MEMO2", "name": "Memorando"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_default_template_must_belong_to_the_type(self):
        from apps.templates.models import Template

        other = DocumentType.objects.create(code="INFORME", name="Informe")
        template = Template.objects.create(document_type=other, name="Plantilla informe")
        memo = DocumentType.objects.get(code="MEMORANDO")
        response = client_for(self.secretaria).patch(
            f"/api/v1/document-types/{memo.id}/", {"default_template": template.id}, format="json"
        )
        self.assertEqual(response.status_code, 400)

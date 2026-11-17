from rest_framework.test import APIClient, APITestCase

from apps.common.testing import client_for, make_office, make_user, seed_permissions_and_roles
from apps.document_types.models import DocumentType
from apps.documents.models import DocumentDraft


class DashboardSummaryTests(APITestCase):
    def setUp(self):
        seed_permissions_and_roles()
        self.ti = make_office("TI", "Tecnologías de la Información")
        self.rrhh = make_office("RRHH", "Gestión de Recursos Humanos")
        self.memo = DocumentType.objects.create(code="MEMORANDO", name="Memorando")
        self.personal = make_user("personal1", role="TRABAJADOR", office=self.ti, level="PERSONAL")
        self.total = make_user("total1", role="TRABAJADOR", office=self.ti, level="TOTAL")
        self.colleague = make_user("colega1", role="TRABAJADOR", office=self.ti, level="PERSONAL")
        self.other = make_user("otro1", role="TRABAJADOR", office=self.rrhh, level="TOTAL")
        self._draft(self.personal)
        self._draft(self.colleague)
        self._draft(self.colleague, confidentiality="CONFIDENTIAL")
        self._draft(self.other, office=self.rrhh)

    def _draft(self, author, office=None, **extra):
        return DocumentDraft.objects.create(
            title="Borrador", document_type=self.memo, office=office or self.ti, author=author, **extra
        )

    @staticmethod
    def _by_key(response):
        return {item["key"]: item for item in response.data["items"]}

    def test_requires_authentication(self):
        self.assertEqual(APIClient().get("/api/v1/dashboard/summary/").status_code, 401)

    def test_personal_view_counts_only_own_drafts_and_has_four_entries(self):
        response = client_for(self.personal).get("/api/v1/dashboard/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["access_level"], "PERSONAL")
        self.assertEqual([i["key"] for i in response.data["items"]],
                         ["para_despacho", "en_proyecto", "no_leidos", "recibidos"])
        self.assertEqual(self._by_key(response)["en_proyecto"]["value"], 1)

    def test_total_view_counts_office_drafts_excluding_confidential_of_others(self):
        response = client_for(self.total).get("/api/v1/dashboard/summary/")
        self.assertEqual(response.data["access_level"], "TOTAL")
        self.assertEqual([i["key"] for i in response.data["items"]],
                         ["para_firma", "borradores", "bandeja_entrada", "delegados", "enviados"])
        # Ve 2 de su oficina (el confidencial de otro compañero no cuenta); no ve los de RR.HH.
        self.assertEqual(self._by_key(response)["borradores"]["value"], 2)

    def test_workflow_counters_are_unavailable_not_zero(self):
        items = self._by_key(client_for(self.total).get("/api/v1/dashboard/summary/"))
        for key in ("para_firma", "bandeja_entrada", "delegados", "enviados"):
            self.assertIsNone(items[key]["value"])
            self.assertFalse(items[key]["available"])

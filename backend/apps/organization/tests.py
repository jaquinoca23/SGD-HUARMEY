from rest_framework.test import APITestCase

from apps.audit.models import AuditLog
from apps.common.testing import client_for, make_office, make_user, seed_permissions_and_roles
from apps.organization.models import Assignment


class OfficeApiTests(APITestCase):
    def setUp(self):
        seed_permissions_and_roles()
        self.root = make_office("OGA", "Oficina General de Administración", kind="GENERAL")
        self.admin = make_user("admin1", role="ADMIN_SISTEMA", office=self.root)
        self.worker = make_user("worker1", role="TRABAJADOR", office=self.root)

    def test_admin_creates_office_and_it_is_audited(self):
        response = client_for(self.admin).post(
            "/api/v1/offices/", {"code": "tes", "name": "Tesorería", "kind": "UNIT", "parent": self.root.id}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["code"], "TES")
        self.assertTrue(AuditLog.objects.filter(action="CREATE", entity_type="organization.Office").exists())

    def test_admin_edits_office(self):
        child = make_office("CONT", "Contabilidad", parent=self.root)
        response = client_for(self.admin).patch(f"/api/v1/offices/{child.id}/", {"name": "Contabilidad General"}, format="json")
        self.assertEqual(response.status_code, 200)
        child.refresh_from_db()
        self.assertEqual(child.name, "Contabilidad General")
        log = AuditLog.objects.filter(action="UPDATE", entity_id=str(child.id)).first()
        self.assertIn("name", log.changes)

    def test_worker_can_read_but_not_write_offices(self):
        client = client_for(self.worker)
        self.assertEqual(client.get("/api/v1/offices/").status_code, 200)
        self.assertEqual(client.post("/api/v1/offices/", {"code": "X", "name": "X"}, format="json").status_code, 403)
        self.assertEqual(client.patch(f"/api/v1/offices/{self.root.id}/", {"name": "Otro"}, format="json").status_code, 403)

    def test_hierarchy_cycle_is_rejected(self):
        child = make_office("CONT", "Contabilidad", parent=self.root)
        response = client_for(self.admin).patch(f"/api/v1/offices/{self.root.id}/", {"parent": child.id}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_duplicate_name_under_same_parent_is_rejected(self):
        make_office("CONT", "Contabilidad", parent=self.root)
        response = client_for(self.admin).post(
            "/api/v1/offices/", {"code": "CONT2", "name": "contabilidad", "parent": self.root.id}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_deactivate_office_with_active_children(self):
        make_office("CONT", "Contabilidad", parent=self.root)
        response = client_for(self.admin).delete(f"/api/v1/offices/{self.root.id}/")
        self.assertEqual(response.status_code, 400)

    def test_tree_endpoint_nests_children(self):
        make_office("CONT", "Contabilidad", parent=self.root)
        response = client_for(self.worker).get("/api/v1/offices/tree/")
        self.assertEqual(response.status_code, 200)
        node = next(n for n in response.data if n["code"] == "OGA")
        self.assertEqual([c["code"] for c in node["children"]], ["CONT"])


class AssignmentTests(APITestCase):
    def setUp(self):
        seed_permissions_and_roles()
        self.ti = make_office("TI", "Tecnologías de la Información")
        self.rrhh = make_office("RRHH", "Gestión de Recursos Humanos")
        self.admin = make_user("admin1", role="ADMIN_SISTEMA", office=self.ti)
        self.worker = make_user("worker1", role="TRABAJADOR", office=self.ti)

    def test_admin_assigns_user_to_office_with_access_level(self):
        response = client_for(self.admin).post(
            "/api/v1/assignments/",
            {"user": self.worker.id, "office": self.rrhh.id, "access_level": "TOTAL", "is_primary": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        # La nueva oficina principal desplaza a la anterior.
        self.assertEqual(Assignment.objects.filter(user=self.worker, is_primary=True, is_active=True).count(), 1)
        self.assertTrue(Assignment.objects.get(user=self.worker, office=self.rrhh).is_primary)

    def test_duplicate_active_assignment_rejected(self):
        response = client_for(self.admin).post(
            "/api/v1/assignments/", {"user": self.worker.id, "office": self.ti.id}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_worker_cannot_create_assignments(self):
        response = client_for(self.worker).post(
            "/api/v1/assignments/", {"user": self.worker.id, "office": self.rrhh.id, "access_level": "TOTAL"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

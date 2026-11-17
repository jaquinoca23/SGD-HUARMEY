from rest_framework.test import APIClient, APITestCase

from apps.audit.models import AuditLog
from apps.common.testing import client_for, make_office, make_user, seed_permissions_and_roles


class AuditTests(APITestCase):
    def setUp(self):
        seed_permissions_and_roles()
        office = make_office("TI", "Tecnologías de la Información")
        self.admin = make_user("admin1", role="ADMIN_SISTEMA", office=office)
        self.worker = make_user("worker1", role="TRABAJADOR", office=office)

    def test_admin_actions_are_recorded_with_actor(self):
        client_for(self.admin).post("/api/v1/offices/", {"code": "NEW", "name": "Nueva oficina"}, format="json")
        log = AuditLog.objects.get(action="CREATE", entity_type="organization.Office")
        self.assertEqual(log.actor_username, "admin1")
        self.assertEqual(log.changes["despues"]["code"], "NEW")

    def test_password_is_never_written_to_audit(self):
        client_for(self.admin).post(
            "/api/v1/users/",
            {"username": "nuevo", "email": "n@ejemplo.invalid", "first_name": "N", "last_name": "U",
             "password": "Contraseña-Segura-12345"},
            format="json",
        )
        for log in AuditLog.objects.filter(entity_type="accounts.User"):
            self.assertNotIn("password", str(log.changes))

    def test_only_audit_viewers_can_read_logs(self):
        AuditLog.objects.create(action="TEST", entity_type="x")
        self.assertEqual(client_for(self.admin).get("/api/v1/audit-logs/").status_code, 200)
        self.assertEqual(client_for(self.worker).get("/api/v1/audit-logs/").status_code, 403)
        self.assertEqual(APIClient().get("/api/v1/audit-logs/").status_code, 401)

    def test_audit_records_are_immutable(self):
        log = AuditLog.objects.create(action="TEST", entity_type="x")
        log.action = "OTRA"
        with self.assertRaises(PermissionError):
            log.save()
        with self.assertRaises(PermissionError):
            log.delete()

    def test_failed_login_is_recorded(self):
        APIClient().post("/api/v1/auth/login/", {"username": "admin1", "password": "incorrecta"}, format="json")
        self.assertTrue(AuditLog.objects.filter(action="LOGIN_FAILED").exists())

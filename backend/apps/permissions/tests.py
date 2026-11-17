from rest_framework.test import APITestCase

from apps.common.testing import client_for, make_office, make_user, seed_permissions_and_roles
from apps.organization.services import access_level_for, total_access_office_ids
from apps.permissions.models import AppPermission, Role, SigningAuthority, UserPermission
from apps.permissions.services import get_user_permission_codes


class PermissionModelTests(APITestCase):
    def setUp(self):
        seed_permissions_and_roles()
        self.office = make_office("TI", "Tecnologías de la Información")

    def test_total_access_does_not_grant_signing_or_approval_permissions(self):
        user = make_user("total1", role="TRABAJADOR", office=self.office, level="TOTAL")
        self.assertEqual(access_level_for(user), "TOTAL")
        self.assertIn(self.office.id, total_access_office_ids(user))
        codes = get_user_permission_codes(user)
        for forbidden in ("documents.sign", "documents.approve", "documents.issue", "documents.annul"):
            self.assertNotIn(forbidden, codes)

    def test_personal_access_can_still_hold_operational_permissions(self):
        user = make_user("personal1", role="JEFE_OFICINA", office=self.office, level="PERSONAL")
        self.assertEqual(access_level_for(user), "PERSONAL")
        self.assertIn("documents.sign", get_user_permission_codes(user))

    def test_signing_authority_is_independent_of_access_level_and_roles(self):
        user = make_user("total2", role="TRABAJADOR", office=self.office, level="TOTAL")
        self.assertFalse(SigningAuthority.objects.filter(user=user).exists())

    def test_direct_permissions_add_to_role_permissions(self):
        user = make_user("worker1", role="TRABAJADOR", office=self.office)
        UserPermission.objects.create(user=user, permission=AppPermission.objects.get(code="audit.view"))
        self.assertIn("audit.view", get_user_permission_codes(user))

    def test_inactive_role_grants_nothing(self):
        user = make_user("worker2", role="TRABAJADOR", office=self.office)
        Role.objects.filter(code="TRABAJADOR").update(is_active=False)
        self.assertNotIn("documents.create", get_user_permission_codes(user))

    def test_superuser_has_every_permission(self):
        user = make_user("root1", superuser=True)
        self.assertEqual(get_user_permission_codes(user), set(AppPermission.objects.values_list("code", flat=True)))


class RoleApiTests(APITestCase):
    def setUp(self):
        seed_permissions_and_roles()
        self.office = make_office("TI", "Tecnologías de la Información")
        self.admin = make_user("admin1", role="ADMIN_SISTEMA", office=self.office)
        self.worker = make_user("worker1", role="TRABAJADOR", office=self.office)

    def test_admin_creates_role_with_permissions(self):
        ids = list(AppPermission.objects.filter(code__in=["documents.create", "users.view"]).values_list("id", flat=True))
        response = client_for(self.admin).post(
            "/api/v1/roles/", {"code": "consulta", "name": "Consulta", "permission_ids": ids}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(sorted(response.data["permission_codes"]), ["documents.create", "users.view"])

    def test_worker_cannot_list_roles(self):
        self.assertEqual(client_for(self.worker).get("/api/v1/roles/").status_code, 403)

    def test_editor_cannot_grant_permissions_they_lack(self):
        editor = make_user("editor1", office=self.office)
        for perm in AppPermission.objects.filter(code__in=["roles.manage"]):
            UserPermission.objects.create(user=editor, permission=perm)
        ids = list(AppPermission.objects.filter(code="documents.sign").values_list("id", flat=True))
        response = client_for(editor).post("/api/v1/roles/", {"code": "X", "name": "X", "permission_ids": ids}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_system_roles_cannot_be_deactivated(self):
        role = Role.objects.get(code="ADMIN_SISTEMA")
        self.assertEqual(client_for(self.admin).delete(f"/api/v1/roles/{role.id}/").status_code, 400)

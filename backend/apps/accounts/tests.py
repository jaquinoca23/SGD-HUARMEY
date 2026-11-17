from django.core.cache import cache
from rest_framework.test import APIClient, APITestCase

from apps.common.testing import TEST_PASSWORD, client_for, make_office, make_user, seed_permissions_and_roles
from apps.permissions.models import AppPermission, UserPermission


class AuthenticationTests(APITestCase):
    def setUp(self):
        cache.clear()  # reinicia el límite de intentos de login entre pruebas
        seed_permissions_and_roles()
        self.office = make_office("TI", "Tecnologías de la Información")
        self.user = make_user("ana", role="TRABAJADOR", office=self.office, level="TOTAL")

    def _login(self, username="ana", password=TEST_PASSWORD):
        return APIClient().post("/api/v1/auth/login/", {"username": username, "password": password}, format="json")

    def test_login_returns_tokens_and_user_context(self):
        response = self._login()
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["access_level"], "TOTAL")
        self.assertEqual(response.data["user"]["primary_office"]["code"], "TI")
        self.assertNotIn("password", response.data["user"])

    def test_wrong_password_is_rejected(self):
        self.assertEqual(self._login(password="incorrecta-123").status_code, 401)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self._login().status_code, 401)

    def test_me_requires_authentication(self):
        self.assertEqual(APIClient().get("/api/v1/auth/me/").status_code, 401)

    def test_me_returns_effective_permissions(self):
        response = client_for(self.user).get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("documents.create", response.data["permissions"])
        self.assertNotIn("documents.sign", response.data["permissions"])

    def test_logout_blacklists_refresh_token(self):
        tokens = self._login().data
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(client.post("/api/v1/auth/logout/", {"refresh": tokens["refresh"]}, format="json").status_code, 204)
        again = APIClient().post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(again.status_code, 401)


class UserManagementTests(APITestCase):
    def setUp(self):
        cache.clear()
        seed_permissions_and_roles()
        self.office = make_office("TI", "Tecnologías de la Información")
        self.admin = make_user("admin1", role="ADMIN_SISTEMA", office=self.office)
        self.worker = make_user("worker1", role="TRABAJADOR", office=self.office)

    def _payload(self, **extra):
        data = {"username": "nuevo", "email": "nuevo@ejemplo.invalid", "first_name": "Nuevo",
                "last_name": "Usuario", "password": TEST_PASSWORD}
        data.update(extra)
        return data

    def test_admin_creates_user_with_hashed_password(self):
        from apps.permissions.models import Role

        role = Role.objects.get(code="TRABAJADOR")
        response = client_for(self.admin).post("/api/v1/users/", self._payload(role_ids=[role.id]), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn("password", response.data)
        from django.contrib.auth import get_user_model

        created = get_user_model().objects.get(username="nuevo")
        self.assertNotEqual(created.password, TEST_PASSWORD)
        self.assertTrue(created.check_password(TEST_PASSWORD))
        self.assertEqual([r.code for r in created.roles.all()], ["TRABAJADOR"])

    def test_weak_password_rejected(self):
        response = client_for(self.admin).post("/api/v1/users/", self._payload(password="12345678"), format="json")
        self.assertEqual(response.status_code, 400)

    def test_worker_cannot_manage_users(self):
        client = client_for(self.worker)
        self.assertEqual(client.get("/api/v1/users/").status_code, 403)
        self.assertEqual(client.post("/api/v1/users/", self._payload(), format="json").status_code, 403)

    def test_anonymous_cannot_list_users(self):
        self.assertEqual(APIClient().get("/api/v1/users/").status_code, 401)

    def test_manager_cannot_grant_permissions_they_lack(self):
        from apps.permissions.models import Role

        manager = make_user("manager1", office=self.office)
        for perm in AppPermission.objects.filter(code__in=["users.view", "users.manage"]):
            UserPermission.objects.create(user=manager, permission=perm)
        admin_role = Role.objects.get(code="ADMIN_SISTEMA")
        response = client_for(manager).post("/api/v1/users/", self._payload(role_ids=[admin_role.id]), format="json")
        self.assertEqual(response.status_code, 400)

    def test_cannot_deactivate_own_account(self):
        response = client_for(self.admin).delete(f"/api/v1/users/{self.admin.id}/")
        self.assertEqual(response.status_code, 400)

    def test_delete_deactivates_instead_of_removing(self):
        response = client_for(self.admin).delete(f"/api/v1/users/{self.worker.id}/")
        self.assertEqual(response.status_code, 204)
        self.worker.refresh_from_db()
        self.assertFalse(self.worker.is_active)

"""Utilidades para pruebas (datos ficticios; contraseña generada por prueba)."""
import io
import secrets

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organization.models import Assignment, Office, Position
from apps.permissions.models import AppPermission, Role
from apps.permissions.seed_data import PERMISSIONS, ROLES

User = get_user_model()
TEST_PASSWORD = secrets.token_urlsafe(14) + "aZ9"


def seed_permissions_and_roles():
    for code, name, category, description in PERMISSIONS:
        AppPermission.objects.get_or_create(code=code, defaults={"name": name, "category": category})
    for code, name, description, perm_codes in ROLES:
        role, _ = Role.objects.get_or_create(code=code, defaults={"name": name, "is_system": True})
        role.permissions.set(AppPermission.objects.filter(code__in=perm_codes))


def make_user(username, *, role=None, office=None, level="PERSONAL", position=None, superuser=False):
    user = User.objects.create_user(
        username=username, email=f"{username}@ejemplo.invalid", password=TEST_PASSWORD,
        first_name=username.title(), last_name="Prueba", is_superuser=superuser, is_staff=superuser,
    )
    if role:
        user.roles.add(Role.objects.get(code=role))
    if office:
        Assignment.objects.create(user=user, office=office, access_level=level, is_primary=True, position=position)
    return user


def make_office(code, name, parent=None, kind="UNIT"):
    return Office.objects.create(code=code, name=name, parent=parent, kind=kind)


def make_position(code="JEFE", name="Jefe", is_head=True):
    return Position.objects.get_or_create(code=code, defaults={"name": name, "is_head": is_head})[0]


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def docx_bytes(text="Prueba") -> bytes:
    from docx import Document

    doc = Document()
    doc.add_paragraph(text)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

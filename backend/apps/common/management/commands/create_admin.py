"""Crea (o actualiza) el administrador del sistema con rol ADMIN_SISTEMA.

La contraseña se pide por consola (no se acepta por argumento para no dejarla en el historial)
o se toma de la variable de entorno HUARMY_ADMIN_PASSWORD (útil para automatizar).
"""
import getpass
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.permissions.models import Role


class Command(BaseCommand):
    help = "Crea el usuario administrador (superusuario + rol ADMIN_SISTEMA)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--first-name", default="Administrador")
        parser.add_argument("--last-name", default="del Sistema")

    def handle(self, *args, **opts):
        User = get_user_model()
        password = os.environ.get("HUARMY_ADMIN_PASSWORD") or getpass.getpass("Contraseña: ")
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages))

        user, created = User.objects.get_or_create(
            username=opts["username"],
            defaults={"email": opts["email"], "first_name": opts["first_name"], "last_name": opts["last_name"]},
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        role = Role.objects.filter(code="ADMIN_SISTEMA").first()
        if role:
            user.roles.add(role)
        else:
            self.stdout.write(self.style.WARNING("Rol ADMIN_SISTEMA no existe: ejecute primero seed_catalog."))
        self.stdout.write(self.style.SUCCESS(f"Administrador {'creado' if created else 'actualizado'}: {user.username}"))

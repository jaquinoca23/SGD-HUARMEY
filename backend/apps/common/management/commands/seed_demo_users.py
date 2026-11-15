"""Crea usuarios FICTICIOS de demostración para probar acceso personal y total.

No hay contraseñas en el código: se usa --password o se genera una aleatoria que se muestra una vez.
Solo para desarrollo. No ejecutar en producción.
"""
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.organization.models import Assignment, Office, Position
from apps.permissions.models import Role

# (usuario, nombres, apellidos, oficina, cargo, nivel, rol)
DEMO_USERS = [
    ("demo.jefe.ti", "Jefe", "Demostración TI", "TI", "JEFE", "TOTAL", "JEFE_OFICINA"),
    ("demo.total.ti", "Trabajador Total", "Demostración TI", "TI", "ESPECIALISTA", "TOTAL", "TRABAJADOR"),
    ("demo.personal.ti", "Trabajador Personal", "Demostración TI", "TI", "ESPECIALISTA", "PERSONAL", "TRABAJADOR"),
    ("demo.personal.rrhh", "Trabajador Personal", "Demostración RR.HH.", "RRHH", "ASISTENTE", "PERSONAL", "TRABAJADOR"),
    ("demo.secretaria", "Secretaría", "Demostración General", "TRAM", "SECRETARIA", "TOTAL", "SECRETARIA_GENERAL"),
]


class Command(BaseCommand):
    help = "Crea usuarios ficticios de demostración (requiere seed_catalog)."

    def add_arguments(self, parser):
        parser.add_argument("--password", help="Contraseña común; si se omite se genera una aleatoria.")

    def handle(self, *args, **opts):
        if not Office.objects.exists():
            raise CommandError("Ejecute primero: python manage.py seed_catalog")
        User = get_user_model()
        password = opts["password"] or secrets.token_urlsafe(12)
        for username, first, last, office_code, pos_code, level, role_code in DEMO_USERS:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@ejemplo.invalid", "first_name": first, "last_name": last},
            )
            user.set_password(password)
            user.is_active = True
            user.save()
            role = Role.objects.get(code=role_code)
            user.roles.add(role)
            Assignment.objects.update_or_create(
                user=user, office=Office.objects.get(code=office_code), is_active=True,
                defaults={"position": Position.objects.get(code=pos_code), "access_level": level, "is_primary": True},
            )
        self.stdout.write(self.style.SUCCESS("Usuarios demo creados: " + ", ".join(u[0] for u in DEMO_USERS)))
        if not opts["password"]:
            self.stdout.write(f"Contraseña generada (guárdela ahora, no se vuelve a mostrar): {password}")

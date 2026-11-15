"""Carga (idempotente) el catálogo base: permisos, roles, oficinas, cargos, tipos documentales
y una plantilla DOCX de demostración claramente marcada como NO OFICIAL."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.document_types.models import DocumentType
from apps.document_types.seed_data import DOCUMENT_TYPES
from apps.organization.models import Office, Position
from apps.organization.seed_data import OFFICES, POSITIONS
from apps.permissions.models import AppPermission, Role
from apps.permissions.seed_data import PERMISSIONS, ROLES
from apps.templates.models import Template
from apps.templates.services import add_version

DEMO_TEMPLATE_NAME = "Plantilla de demostración (NO OFICIAL)"


def build_demo_docx() -> bytes:
    from docx import Document

    doc = Document()
    doc.add_heading("PLANTILLA DE DEMOSTRACIÓN — NO OFICIAL", level=1)
    doc.add_paragraph(
        "Este archivo es solo un ejemplo técnico de HUARMY SGD Fase 01. No corresponde a un formato "
        "aprobado por la Municipalidad Provincial de Huarmey."
    )
    for line in ("N.°: {{numero}}", "Fecha: {{fecha}}", "Para: {{destinatario}}",
                 "De: {{remitente}}", "Asunto: {{asunto}}"):
        doc.add_paragraph(line)
    doc.add_paragraph("{{contenido}}")
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


class Command(BaseCommand):
    help = "Carga permisos, roles, oficinas, cargos, tipos documentales y plantilla demo."

    @transaction.atomic
    def handle(self, *args, **options):
        # Permisos y roles
        for code, name, category, description in PERMISSIONS:
            AppPermission.objects.update_or_create(
                code=code, defaults={"name": name, "category": category, "description": description}
            )
        for code, name, description, perm_codes in ROLES:
            role, _ = Role.objects.update_or_create(
                code=code, defaults={"name": name, "description": description, "is_system": True, "is_active": True}
            )
            role.permissions.set(AppPermission.objects.filter(code__in=perm_codes))

        # Oficinas (padres antes que hijos: la lista ya está ordenada así)
        by_code = {}
        for order, (code, name, kind, parent_code) in enumerate(OFFICES):
            parent = by_code.get(parent_code) if parent_code else None
            office, _ = Office.objects.update_or_create(
                code=code, defaults={"name": name, "kind": kind, "parent": parent, "sort_order": order, "is_active": True}
            )
            by_code[code] = office

        for code, name, is_head in POSITIONS:
            Position.objects.update_or_create(code=code, defaults={"name": name, "is_head": is_head})

        # Tipos documentales
        types = {}
        for order, (code, name, signature, scope, multiple) in enumerate(DOCUMENT_TYPES):
            types[code], _ = DocumentType.objects.update_or_create(
                code=code,
                defaults={"name": name, "requires_signature": signature, "issuance_scope": scope,
                          "allows_multiple_recipients": multiple, "sort_order": order, "is_active": True},
            )

        # Plantilla de demostración para Memorando (solo si aún no existe)
        memo = types["MEMORANDO"]
        template, created = Template.objects.get_or_create(
            document_type=memo, office=None, is_active=True,
            defaults={"name": DEMO_TEMPLATE_NAME,
                      "description": "Ejemplo técnico. Reemplazar por la plantilla oficial."},
        )
        if created:
            upload = SimpleUploadedFile("plantilla-demo-no-oficial.docx", build_demo_docx())
            add_version(template, upload, user=None, version_label="demo", is_official=False,
                        notes="Plantilla de demostración no oficial.", set_current=True)
        if memo.default_template_id is None:
            memo.default_template = template
            memo.save(update_fields=["default_template", "updated_at"])

        self.stdout.write(self.style.SUCCESS(
            f"Catálogo listo: {Office.objects.count()} oficinas, {DocumentType.objects.count()} tipos "
            f"documentales, {Role.objects.count()} roles, {AppPermission.objects.count()} permisos."
        ))

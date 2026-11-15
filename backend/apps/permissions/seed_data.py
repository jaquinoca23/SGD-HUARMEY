"""Catálogo inicial de permisos y roles (datos de demostración editables)."""

SIGNATURE_NOTE = "Reservado: aún no se aplica en endpoints (fases posteriores)."

PERMISSIONS = [
    # (código, nombre, categoría, descripción)
    ("admin.access", "Acceder al panel administrativo", "ADMINISTRATION", ""),
    ("users.view", "Consultar usuarios y asignaciones", "ADMINISTRATION", ""),
    ("users.manage", "Gestionar usuarios y asignaciones", "ADMINISTRATION", ""),
    ("offices.manage", "Gestionar oficinas y cargos", "ADMINISTRATION", ""),
    ("roles.manage", "Gestionar roles y permisos", "ADMINISTRATION", ""),
    ("document_types.manage", "Gestionar tipos documentales", "ADMINISTRATION", ""),
    ("templates.manage", "Gestionar plantillas documentales", "ADMINISTRATION", ""),
    ("audit.view", "Consultar la auditoría", "ADMINISTRATION", ""),
    ("documents.create", "Crear borradores de documentos", "OPERATIONAL", ""),
    ("documents.derive_office", "Derivar a compañeros de la misma oficina", "OPERATIONAL", "Reservado para fase 2."),
    ("documents.review", "Revisar / dar visto bueno", "OPERATIONAL", "Reservado para fase 2."),
    ("documents.receive", "Confirmar recepción en bandeja", "OPERATIONAL", "Reservado para fase 2."),
    ("documents.sign", "Firmar documentos", "SIGNATURE", SIGNATURE_NOTE),
    ("documents.approve", "Aprobar documentos", "SIGNATURE", SIGNATURE_NOTE),
    ("documents.issue", "Emitir documentos", "SIGNATURE", SIGNATURE_NOTE),
    ("documents.annul", "Anular documentos", "SIGNATURE", SIGNATURE_NOTE),
]

ADMIN_CODES = ["admin.access", "users.view", "users.manage", "offices.manage", "roles.manage",
               "document_types.manage", "templates.manage", "audit.view", "documents.create"]

ROLES = [
    # (código, nombre, descripción, permisos)
    ("ADMIN_SISTEMA", "Administrador del sistema", "Administración técnica del catálogo y accesos.", ADMIN_CODES),
    ("SECRETARIA_GENERAL", "Secretaría General", "Administra tipos documentales y plantillas.",
     ["admin.access", "document_types.manage", "templates.manage", "documents.create"]),
    ("JEFE_OFICINA", "Jefe o encargado de oficina", "Permisos operativos y de firma (requiere además una competencia de firma registrada).",
     ["documents.create", "documents.derive_office", "documents.review", "documents.receive",
      "documents.sign", "documents.approve", "documents.issue"]),
    ("TRABAJADOR", "Trabajador", "Permisos operativos básicos.",
     ["documents.create", "documents.derive_office", "documents.receive"]),
]

"""Interfaces previstas entre HUARMY Web/Django y el agente de escritorio SGDGuarmail.

IMPORTANTE: son solo contratos de diseño. Fase 01 no implementa el agente, ni el bloqueo
de edición, ni la transferencia de versiones. Ningún endpoint usa todavía estas interfaces.
"""
from dataclasses import dataclass
from typing import Optional, Protocol

# Flujo previsto (ver docs/ARQUITECTURA.md y desktop/SGDGuarmail/README.md)
PLANNED_FLOW = [
    "1. El usuario elige un tipo documental en HUARMY Web (React).",
    "2. Django resuelve la plantilla vigente aplicable.",
    "3. SGDGuarmail crea el DOCX en la carpeta 'H Documentos' del usuario de Windows.",
    "4. SGDGuarmail abre el documento en Microsoft Word.",
    "5. El usuario edita y guarda localmente (el borrador puede editarse sin internet).",
    "6. SGDGuarmail detecta los cambios locales.",
    "7. Solo un usuario edita a la vez mediante un bloqueo controlado por el servidor.",
    "8. El usuario finaliza el documento desde HUARMY Web.",
    "9. El agente transfiere la versión al servidor para revisión y aprobación.",
]


@dataclass(frozen=True)
class TemplateDescriptor:
    template_version_id: int
    document_type_code: str
    version_number: int
    checksum_sha256: str
    download_path: str


@dataclass(frozen=True)
class DraftLease:
    draft_public_id: str
    locked_by_user_id: int
    expires_at_iso: str


class AgentGateway(Protocol):
    """Operaciones que el servidor ofrecerá al agente (fase posterior)."""

    def get_template_for_draft(self, draft_public_id: str) -> Optional[TemplateDescriptor]: ...

    def acquire_edit_lock(self, draft_public_id: str, user_id: int) -> DraftLease: ...

    def release_edit_lock(self, draft_public_id: str, user_id: int) -> None: ...

    def upload_version(self, draft_public_id: str, user_id: int, docx_bytes: bytes, sha256: str) -> int: ...

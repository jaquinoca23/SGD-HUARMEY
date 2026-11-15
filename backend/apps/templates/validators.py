"""Validación de archivos DOCX subidos como plantilla."""
import zipfile

from django.conf import settings
from django.core.exceptions import ValidationError

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_MAX_UNCOMPRESSED = 50 * 1024 * 1024  # defensa básica contra "zip bombs"


def validate_docx_upload(uploaded):
    max_bytes = settings.TEMPLATE_MAX_UPLOAD_MB * 1024 * 1024
    name = (getattr(uploaded, "name", "") or "").lower()
    if not name.endswith(".docx"):
        raise ValidationError("Solo se permiten archivos .docx.")
    if uploaded.size > max_bytes:
        raise ValidationError(f"El archivo supera el máximo de {settings.TEMPLATE_MAX_UPLOAD_MB} MB.")
    if uploaded.size == 0:
        raise ValidationError("El archivo está vacío.")

    uploaded.seek(0)
    if uploaded.read(4) != b"PK\x03\x04":
        raise ValidationError("El archivo no es un DOCX válido.")
    uploaded.seek(0)
    try:
        with zipfile.ZipFile(uploaded) as archive:
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ValidationError("El archivo no tiene la estructura de un documento Word.")
            if any(n.lower().endswith("vbaproject.bin") for n in names):
                raise ValidationError("No se permiten documentos con macros.")
            if sum(i.file_size for i in archive.infolist()) > _MAX_UNCOMPRESSED:
                raise ValidationError("El contenido descomprimido es demasiado grande.")
    except zipfile.BadZipFile:
        raise ValidationError("El archivo está dañado o no es un DOCX válido.")
    finally:
        uploaded.seek(0)
    return uploaded

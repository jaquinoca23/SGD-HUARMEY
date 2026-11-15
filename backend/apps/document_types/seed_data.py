"""Catálogo inicial de tipos documentales. Los valores de firma/ámbito son una propuesta
de demostración que Secretaría General debe validar según la normativa vigente."""

# (código, nombre, requiere_firma, ámbito, destinatarios_múltiples)
DOCUMENT_TYPES = [
    ("MEMORANDO", "Memorando", True, "INTERNAL", False),
    ("MEMORANDO_MULTIPLE", "Memorando múltiple", True, "INTERNAL", True),
    ("INFORME", "Informe", True, "INTERNAL", False),
    ("INFORME_TECNICO", "Informe técnico", True, "INTERNAL", False),
    ("INFORME_LEGAL", "Informe legal", True, "INTERNAL", False),
    ("INFORME_ADMINISTRATIVO", "Informe administrativo", True, "INTERNAL", False),
    ("OFICIO", "Oficio", True, "EXTERNAL", False),
    ("OFICIO_MULTIPLE", "Oficio múltiple", True, "EXTERNAL", True),
    ("ACTA", "Acta", True, "INTERNAL", True),
    ("COMUNICADO_OFICIAL", "Comunicado oficial", True, "EXTERNAL", True),
    ("RESOLUCION_ALCALDIA", "Resolución de Alcaldía", True, "NORMATIVE", False),
    ("RESOLUCION_GERENCIAL", "Resolución gerencial", True, "NORMATIVE", False),
    ("RESOLUCION_SUBGERENCIAL", "Resolución subgerencial", True, "NORMATIVE", False),
    ("ORDENANZA_MUNICIPAL", "Ordenanza municipal", True, "NORMATIVE", False),
    ("ACUERDO_CONCEJO", "Acuerdo de concejo", True, "NORMATIVE", False),
    ("DECRETO_ALCALDIA", "Decreto de Alcaldía", True, "NORMATIVE", False),
    ("DIRECTIVA", "Directiva", True, "INTERNAL", True),
    ("PLAN_TRABAJO", "Plan de trabajo", True, "INTERNAL", False),
    ("REGLAMENTO", "Reglamento", True, "NORMATIVE", False),
    ("BORRADOR", "Borrador", False, "OFFICE", False),
    ("PROVEIDO", "Proveído", False, "OFFICE", False),
    ("DERIVACION_INTERNA", "Derivación interna", False, "OFFICE", False),
    ("ACUSE_RECEPCION", "Acuse de recepción", False, "INTERNAL", False),
]

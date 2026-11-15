"""Catálogo institucional base de la Municipalidad Provincial de Huarmey (según el encargo).

Es una base editable: debe ajustarse al ROF vigente. Las oficinas generales y gerencias se
cargan como raíces (sin superior) porque el encargo no define su dependencia jerárquica.
"""

# (código, nombre, tipo, código_superior)
OFFICES = [
    # Órganos de gobierno y dirección
    ("CM", "Concejo Municipal", "GOVERNING", None),
    ("ALC", "Alcaldía", "GOVERNING", None),
    ("GM", "Gerencia Municipal", "GOVERNING", None),
    # Oficina General de Atención al Ciudadano y Gestión Documentaria
    ("OGACGD", "Oficina General de Atención al Ciudadano y Gestión Documentaria", "GENERAL", None),
    ("COM-IMG", "Comunicaciones e Imagen Institucional", "UNIT", "OGACGD"),
    ("ARCH", "Archivo Central", "UNIT", "OGACGD"),
    ("TRAM", "Trámite Documentario", "UNIT", "OGACGD"),
    # Oficina General de Administración
    ("OGA", "Oficina General de Administración", "GENERAL", None),
    ("CONT", "Contabilidad", "UNIT", "OGA"),
    ("ABAST", "Abastecimiento", "UNIT", "OGA"),
    ("TES", "Tesorería", "UNIT", "OGA"),
    ("RRHH", "Gestión de Recursos Humanos", "UNIT", "OGA"),
    # Asesoría Jurídica
    ("OGAJ", "Oficina General de Asesoría Jurídica", "GENERAL", None),
    # Planeamiento y Presupuesto
    ("OGPP", "Oficina General de Planeamiento y Presupuesto", "GENERAL", None),
    ("PMI", "Planeamiento, Modernización e Inversiones", "UNIT", "OGPP"),
    ("TI", "Tecnologías de la Información", "UNIT", "OGPP"),
    ("PPTO", "Presupuesto", "UNIT", "OGPP"),
    # Gerencias
    ("GAT", "Gerencia de Administración Tributaria", "MANAGEMENT", None),
    ("RENTAS", "Rentas", "UNIT", "GAT"),
    ("FTEC", "Fiscalización Tributaria y Ejecución Coactiva", "UNIT", "GAT"),
    ("GDE", "Gerencia de Desarrollo Económico", "MANAGEMENT", None),
    ("DET", "Desarrollo Económico y Turismo", "UNIT", "GDE"),
    ("PCF", "Promoción Comercial y Fiscalización", "UNIT", "GDE"),
    ("GINF", "Gerencia de Infraestructura", "MANAGEMENT", None),
    ("OOPP", "Obras Públicas", "UNIT", "GINF"),
    ("ESTPROY", "Estudios y Proyectos", "UNIT", "GINF"),
    ("GGT", "Gerencia de Gestión Territorial", "MANAGEMENT", None),
    ("FOP", "Formalización y Obras Privadas", "UNIT", "GGT"),
    ("GRD", "Gestión de Riesgos de Desastres", "UNIT", "GGT"),
    ("GSCGA", "Gerencia de Servicios a la Ciudad y Gestión Ambiental", "MANAGEMENT", None),
    ("TRANSP", "Transportes", "UNIT", "GSCGA"),
    ("GAMB", "Gestión Ambiental", "UNIT", "GSCGA"),
    ("SEGCIU", "Seguridad Ciudadana", "UNIT", "GSCGA"),
    ("SERVMUN", "Servicios Municipales", "UNIT", "GSCGA"),
    ("GDS", "Gerencia de Desarrollo Social", "MANAGEMENT", None),
    ("SSPV", "Servicios Sociales y Participación Vecinal", "UNIT", "GDS"),
    ("PROGSOC", "Programas Sociales", "UNIT", "GDS"),
    # Otros órganos
    ("OCI", "Órgano de Control Institucional", "OTHER", None),
    ("PPM", "Procuraduría Pública Municipal", "OTHER", None),
    ("CCLP", "Consejo de Coordinación Local Provincial", "OTHER", None),
    ("JDV", "Junta de Delegados Vecinales", "OTHER", None),
]

# (código, nombre, es_jefatura)
POSITIONS = [
    ("JEFE", "Jefe / Gerente de la dependencia", True),
    ("ENCARGADO", "Encargado de la dependencia", True),
    ("ESPECIALISTA", "Especialista", False),
    ("ASISTENTE", "Asistente administrativo", False),
    ("SECRETARIA", "Secretaria", False),
]

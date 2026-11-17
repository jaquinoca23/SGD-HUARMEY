# HUARMY SGD — Arquitectura (Fase 01)

## 1. Visión general
```
React + TS (Vite)  ──HTTP/JSON, JWT──▶  Django REST API (/api/v1)  ──ORM──▶  PostgreSQL
   frontend/                              backend/                          docker-compose
                                              ▲
                          (futuro) SGDGuarmail (C#/.NET WPF) ── mismo API
```

## 2. Versiones (rangos declarados; ver "Estado de verificación")
| Componente | Versión |
|---|---|
| Python | 3.12 o 3.13 |
| Django | 5.2 LTS |
| Django REST Framework | 3.16 |
| SimpleJWT | 5.5 |
| drf-spectacular (OpenAPI) | 0.28+ |
| PostgreSQL | 16 (imagen Docker) |
| Node.js | 20 LTS o superior |
| React / React Router | 18.3 / 6.28 |
| Vite / TypeScript / Tailwind | 6 / 5.6 / 3.4 |

## 3. Módulos del backend
| App | Contenido |
|---|---|
| `accounts` | Usuario personalizado, login/logout, perfil, CRUD de usuarios. |
| `organization` | `Office` (jerarquía padre-hijo), `Position`, `Assignment` (usuario+oficina+cargo+nivel de acceso). |
| `permissions` | `AppPermission`, `Role`, permisos directos, `SigningAuthority`. |
| `document_types` | Catálogo de tipos (firma, ámbito, destinatarios múltiples, plantilla predeterminada). |
| `templates` (label `doc_templates`) | `Template` y `TemplateVersion` (DOCX, SHA-256, inmutables). |
| `documents` | `DocumentDraft` y reglas de visibilidad. |
| `audit` | `AuditLog` de solo adición. |
| `agent_integration` | Contratos y estado de la futura integración. |
| `common` | Modelo base, paginación, permisos por acción, mixin de auditoría, comandos de carga. |

## 4. Principio central: tres ejes independientes
1. **Visibilidad** (`Assignment.access_level`: PERSONAL / TOTAL): qué documentos se ven.
2. **Permisos operativos** (`Role` + permisos directos): qué acciones se pueden usar.
3. **Competencia de firma** (`SigningAuthority`): quién puede ser firmante oficial en una oficina.

El acceso total **no** concede firmar, aprobar, emitir ni anular (lo cubre una prueba automatizada).
Los permisos `documents.sign/approve/issue/annul` y `SigningAuthority` están modelados, pero **no se
aplican aún** porque el flujo de firma no existe en esta fase. No se simulan firmas digitales.

### Reglas de visibilidad (`documents/services.py`)
- Personal: documentos que generó o tiene asignados.
- Total: además los de su oficina, excepto los confidenciales (solo autor y asignado).
- Un documento ajeno responde 404, no 403, para no revelar su existencia.

## 5. Seguridad implementada
- Contraseñas con el hasher de Django; validadores (mínimo 10 caracteres).
- JWT de acceso (15 min) y refresh rotativo con lista negra; logout invalida el refresh.
- Límite de 10 intentos/min en login; intentos fallidos auditados.
- `ActionPermission` **falla cerrado**: una acción sin permiso declarado se deniega.
- Sin escalada de privilegios: no se pueden conceder permisos que el actor no posee.
- Superusuarios solo modificables por superusuarios; no se puede desactivar la propia cuenta.
- CORS restringido a `CORS_ALLOWED_ORIGINS`; secretos solo por entorno; `SECRET_KEY` validada en producción.
- Plantillas: extensión `.docx`, tamaño máximo, firma ZIP, estructura Word, sin macros, límite descomprimido;
  almacenadas fuera de URLs públicas; descarga solo por vista con control por objeto (oficina) y auditoría.
- Auditoría de altas, cambios (antes/después), desactivaciones, descargas e inicios de sesión; nunca guarda contraseñas.
- Las bajas son lógicas (`is_active=False`).

### Compromiso conocido: almacenamiento de tokens
El frontend guarda los tokens en `sessionStorage` (se pierden al cerrar la pestaña). Es vulnerable a XSS
a diferencia de cookies HttpOnly. Antes de producción se recomienda evaluarlas junto con protección CSRF.

## 6. Reglas documentales: estado
| Regla | Fase 01 |
|---|---|
| Derivar a compañeros de la misma oficina | Solo validado al asignar un borrador (`assigned_to`). |
| Firmante único, vistos buenos, devolución, bandeja, recibido, plazos, numeración | **Pendiente (Fase 2+)**; permisos reservados. |
| Versiones firmadas inmutables | Solo `TemplateVersion` es inmutable; documentos firmados pendientes. |

## 7. Integración futura con SGDGuarmail
Ver `desktop/SGDGuarmail/README.md` y `backend/apps/agent_integration/interfaces.py`. No implementada.

## 8. API
Prefijo `/api/v1/`. Documentación OpenAPI: `/api/schema/` y Swagger en `/api/docs/` (solo si `ENABLE_API_DOCS=True`).
Recursos: `auth/*`, `users`, `offices` (+`tree`), `positions`, `assignments`, `permissions`, `roles`,
`signing-authorities`, `document-types`, `templates` (+`versions`, `set-current`), `template-versions` (+`download`),
`drafts`, `audit-logs`, `integration/status`. Paginación por página (20; máx. 100).

## 8b. Interfaz principal (inicio)
Cabecera (logotipo configurable, oficina, usuario, nivel de acceso, Salir), barra de menú superior
(Configuración, Documentos, Mesa de partes, Consultas, Consultas generales), panel de contadores y banner,
y pie con unidad orgánica. El panel depende del nivel de acceso de la oficina principal
(`GET /api/v1/dashboard/summary/`):
- **Acceso personal:** Para despacho · En proyecto · No leídos · Recibidos.
- **Acceso total:** Para firma · Borradores · Bandeja de entrada · Delegados · Enviados.

Solo «En proyecto» y «Borradores» tienen datos reales en la Fase 01 (borradores visibles según las reglas de
visibilidad). El resto devuelve `value: null` y la interfaz muestra «—», no un cero. Los submenús de fases
posteriores aparecen como «Próximamente». La bandeja de entrada del acceso total mostrará más adelante un
desglose por plazo (tres indicadores de color); requiere la lógica de plazos y alertas de la Fase 2.
El diseño es propio: no usa logotipos, mascotas ni textos de otras entidades.

## 9. Estado de verificación
Ver la sección final del README. Resumen: sintaxis Python comprobada; el resto **no se ejecutó** en el
entorno de generación (sin Django, PostgreSQL ni paquetes de Node disponibles).

# SGDGuarmail (agente de escritorio) — SOLO ESTRUCTURA, NO IMPLEMENTADO

> **Estado en la Fase 01: no existe ejecutable ni código funcional.** Esta carpeta solo reserva la
> estructura y documenta el diseño previsto. Nada aquí funciona todavía.

## Tecnología prevista
C# con .NET (versión LTS vigente al iniciar la fase) y WPF para Windows. Arquitectura modular.

## Módulos previstos (carpetas vacías aún no creadas, para no aparentar funcionalidad)
| Módulo | Responsabilidad |
|---|---|
| `SGDGuarmail.App` | Interfaz WPF, icono de bandeja, inicio de sesión. |
| `SGDGuarmail.Core` | Reglas: flujo de borrador, estados, bloqueos. |
| `SGDGuarmail.Api` | Cliente HTTP de la API de HUARMY (`/api/v1`). |
| `SGDGuarmail.Storage` | Carpeta `H Documentos` del usuario y base local de borradores. |
| `SGDGuarmail.Word` | Apertura en Word y detección de guardados. |
| `SGDGuarmail.Sync` | Sincronización y transferencia de versiones al servidor. |

## Flujo previsto
1. El usuario elige un tipo documental en HUARMY Web.
2. Django resuelve la plantilla vigente (`resolve_template_version`).
3. SGDGuarmail crea el DOCX en `H Documentos` del usuario de Windows.
4. Lo abre en Microsoft Word.
5. El usuario edita y guarda localmente (funciona sin internet).
6. SGDGuarmail detecta los cambios.
7. Solo un usuario edita a la vez, mediante un bloqueo emitido por el servidor.
8. El usuario finaliza el documento desde HUARMY Web.
9. El agente transfiere la versión al servidor para revisión y aprobación.

Los borradores viven principalmente en el equipo local; los documentos presentados, emitidos y firmados
se conservan en el repositorio institucional.

## Lo que ya existe en el servidor (Fase 01)
- `DocumentDraft`: metadatos del borrador, versión de plantilla asignada y campos `locked_by` / `lock_expires_at` reservados.
- `GET /api/v1/templates/…` y `GET /api/v1/template-versions/{id}/download/`: obtención controlada de plantillas.
- `GET /api/v1/integration/status/`: informa que el agente **no** está implementado.
- Contratos de diseño en `backend/apps/agent_integration/interfaces.py`.

## Pendiente de definir antes de implementar
Autenticación del agente (flujo de tokens), endpoints de bloqueo y subida de versiones, política de
resolución de conflictos sin conexión, firma digital con validez jurídica (certificados, no imágenes) y
distribución/actualización del instalador.

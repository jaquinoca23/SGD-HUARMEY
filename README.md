# HUARMY SGD — Fase 01

Base del sistema de gestión documental de la Municipalidad Provincial de Huarmey (Áncash, Perú).
Incluye autenticación, oficinas jerárquicas, roles y permisos, tipos documentales, plantillas DOCX
versionadas, registro inicial de borradores, auditoría y la estructura para la futura app SGDGuarmail.

> **Leer primero la sección [Estado de verificación](#estado-de-verificación).** Este paquete se generó
> en un entorno sin Django, PostgreSQL ni paquetes de Node, de modo que el código **no se ha ejecutado**
> todavía. Siga los pasos y ejecute las pruebas en su equipo.

## Estructura
```
HUARMY-SGD/
├── backend/          Django + DRF (apps: accounts, organization, permissions, document_types,
│                     templates, documents, audit, agent_integration, common)
├── frontend/         React + TypeScript + Vite + Tailwind
├── desktop/SGDGuarmail/   Solo documentación del agente futuro (NO implementado)
├── database/         Notas de base de datos
├── docs/ARQUITECTURA.md
├── docker-compose.yml     PostgreSQL 16
└── .env.example           Variables para docker-compose
```

## Requisitos en Windows
- [Python 3.12 o 3.13](https://www.python.org/downloads/) (marque «Add python.exe to PATH»)
- [Node.js 20 LTS o superior](https://nodejs.org/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para PostgreSQL)
- [Visual Studio Code](https://code.visualstudio.com/) y Git

## Instalación paso a paso (PowerShell, dentro de la carpeta del proyecto)

Abra la carpeta `HUARMY-SGD` en VS Code (*Archivo → Abrir carpeta*) y use *Terminal → Nuevo terminal*.

### 1. Base de datos
```powershell
Copy-Item .env.example .env
notepad .env            # escriba una DB_PASSWORD propia
docker compose up -d
docker compose ps       # el servicio "db" debe figurar como healthy
```

### 2. Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # si PowerShell lo bloquea: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```
En `backend\.env` complete:
- `DJANGO_SECRET_KEY`: genere una con `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`
- `DB_PASSWORD`: **la misma** que puso en el `.env` de la raíz.

### 3. Migraciones
Las migraciones no vienen pre-generadas (ver Estado de verificación). Genérelas y aplíquelas:
```powershell
python manage.py makemigrations accounts organization permissions document_types doc_templates documents audit
python manage.py migrate
```
> La app `templates` usa la etiqueta `doc_templates`. Si `makemigrations` reporta dependencias circulares
> entre `document_types` y `doc_templates`, ejecute `python manage.py makemigrations` sin argumentos.

### 4. Datos iniciales
```powershell
python manage.py seed_catalog          # permisos, roles, oficinas, cargos, 23 tipos documentales, plantilla demo NO OFICIAL
python manage.py create_admin --username admin --email admin@ejemplo.invalid
                                        # pide la contraseña por consola (mín. 10 caracteres)
python manage.py seed_demo_users       # OPCIONAL, solo desarrollo: 5 usuarios ficticios; muestra una contraseña aleatoria
```
Usuarios demo: `demo.jefe.ti`, `demo.total.ti` (acceso total), `demo.personal.ti` (acceso personal),
`demo.personal.rrhh`, `demo.secretaria`. Con ellos se comprueba la diferencia entre acceso personal y total.

### 5. Iniciar el backend
```powershell
python manage.py runserver
```
API en <http://localhost:8000/api/v1/> · Swagger en <http://localhost:8000/api/docs/> · esquema OpenAPI en `/api/schema/`.

### 6. Frontend (otra terminal)
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Abra <http://localhost:5173> e ingrese con `admin`.

### Logotipo institucional
No se incluye logotipo. Copie su archivo a `frontend/public/` y ponga su ruta en `VITE_INSTITUTION_LOGO_URL`
(ej. `/logo-institucional.png`) en `frontend/.env`.

## Pantalla de inicio
Panel de contadores distinto según el nivel de acceso (personal o total), menú superior, banner y pie con la
unidad orgánica. Pruébelo entrando con `demo.personal.ti` y con `demo.total.ti`. Los contadores que dependen del
flujo documental (despacho, bandejas, enviados) muestran «—» hasta la Fase 2. Variable opcional del nombre de sede:
`VITE_INSTITUTION_SEDE` en `frontend/.env`.

## Pruebas
```powershell
cd backend
python manage.py test apps          # usa PostgreSQL: el usuario necesita permiso para crear la base test_*
cd ..\frontend
npm run typecheck
```
Cubren: autenticación, permisos por oficina, acceso personal/total (y que el total no da permisos de firma),
oficinas (creación, edición, ciclos, duplicados), tipos documentales, plantillas (subida, validación, versiones,
privacidad por oficina, descarga), borradores y auditoría.

## Permisos incluidos
`admin.access`, `users.view/manage`, `offices.manage`, `roles.manage`, `document_types.manage`,
`templates.manage`, `audit.view`, `documents.create`, y reservados para fases posteriores:
`documents.derive_office/review/receive/sign/approve/issue/annul`.

## Alcance de la Fase 01 (y lo que NO hay)
- **Sí:** lo descrito arriba, 10 pantallas, API REST versionada con OpenAPI.
- **No:** flujo de derivación, vistos buenos, firma, numeración, bandejas, plazos y alertas; SGDGuarmail
  (solo documentación); firma digital con validez jurídica.
- El catálogo de oficinas es una base editable que debe contrastarse con el ROF vigente. Los valores de firma y
  ámbito de los tipos documentales son una propuesta a validar por Secretaría General.
- La plantilla DOCX de demostración está marcada **NO OFICIAL**.

## Estado de verificación

| Criterio de aceptación | Estado |
|---|---|
| Sintaxis de los 85 archivos Python | ✅ comprobada (`compileall`) |
| Django arranca sin errores | ⚠️ **No ejecutado** |
| Conexión a PostgreSQL | ⚠️ **No ejecutado** |
| Migraciones | ⚠️ **No generadas ni ejecutadas** |
| Pruebas automatizadas (backend) | ⚠️ **Escritas, no ejecutadas** |
| Compilación TypeScript / arranque de React | ⚠️ **No ejecutado** |
| Login, gestión de oficinas/usuarios, plantillas de extremo a extremo | ⚠️ **No probado** |

Es probable que la primera ejecución muestre algún error menor (importaciones, migraciones, tipos). Si ocurre,
pegue el mensaje completo para corregirlo antes de avanzar a la Fase 2.

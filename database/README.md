# Base de datos

El esquema se define con modelos de Django; las migraciones se generan y aplican con
`python manage.py makemigrations` y `python manage.py migrate` (ver README principal).

Las migraciones **no vienen pre-generadas en este paquete** porque se crearon sin poder ejecutar
Django. Se generan en su equipo con `makemigrations` (paso 5 del README) y conviene
subirlas al repositorio una vez creadas.

PostgreSQL se levanta con `docker-compose.yml` (raíz). Los datos persisten en el volumen
`huarmy_pgdata`. Para reiniciar la base desde cero: `docker compose down -v`.

Tablas principales: `accounts_user`, `organization_office` (jerarquía por `parent_id`),
`organization_position`, `organization_assignment` (usuario + oficina + cargo + nivel de acceso),
`permissions_apppermission`, `permissions_role`, `permissions_signingauthority`,
`document_types_documenttype`, `doc_templates_template`, `doc_templates_templateversion`,
`documents_documentdraft`, `audit_auditlog`.

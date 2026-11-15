import { FormEvent, useState } from "react";

import { ACCESS_LEVEL_LABEL } from "../../app/config";
import { useAuth } from "../../app/AuthContext";
import { useList } from "../../app/useList";
import { Alert, Badge, DataTable, Field, Modal, PageHeader, Pagination, SearchBox, Spinner } from "../../components/ui";
import { assignmentsApi, officesApi, permissionsApi, positionsApi, rolesApi, usersApi } from "../../services/api";
import { errorMessage } from "../../services/http";
import type { AccessLevel, AppPermission, Assignment, Office, Position, Role, User } from "../../types";

interface Form {
  id?: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  document_number: string;
  phone: string;
  is_active: boolean;
  password: string;
  role_ids: number[];
  extra_permission_ids: number[];
}

const empty: Form = {
  username: "", email: "", first_name: "", last_name: "", document_number: "", phone: "",
  is_active: true, password: "", role_ids: [], extra_permission_ids: [],
};

function toggle(list: number[], id: number) {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
}

export function UsersPage() {
  const { can } = useAuth();
  const canManage = can("users.manage");
  const list = useList<User>(usersApi.list);
  const [form, setForm] = useState<Form | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [perms, setPerms] = useState<AppPermission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [assign, setAssign] = useState<User | null>(null);

  const openForm = async (user?: User) => {
    setError(null);
    try {
      const [r, p] = await Promise.all([rolesApi.list({ page_size: 100 }), permissionsApi.list()]);
      setRoles(r.results.filter((x) => x.is_active));
      setPerms(p);
      setForm(
        user
          ? { ...empty, id: user.id, username: user.username, email: user.email, first_name: user.first_name, last_name: user.last_name,
              document_number: user.document_number ?? "", phone: user.phone, is_active: user.is_active,
              role_ids: user.role_ids, extra_permission_ids: user.extra_permission_ids }
          : empty,
      );
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    setError(null);
    const { id, password, document_number, ...rest } = form;
    const body: Record<string, unknown> = { ...rest, document_number: document_number || null };
    if (password) body.password = password;
    if (id) delete body.username; // el nombre de usuario no se cambia
    try {
      if (id) await usersApi.update(id, body);
      else await usersApi.create(body);
      setForm(null);
      setNotice("Usuario guardado.");
      list.reload();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const deactivate = async (u: User) => {
    if (!window.confirm(`¿Desactivar la cuenta de ${u.full_name}?`)) return;
    try {
      await usersApi.remove(u.id);
      setNotice("Usuario desactivado.");
      list.reload();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const set = (key: keyof Form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm(form && { ...form, [key]: e.target.value });

  return (
    <div>
      <PageHeader
        title="Usuarios"
        subtitle="Cuentas del sistema. La oficina, el cargo y el nivel de acceso se asignan por separado de los roles y permisos."
        actions={canManage && <button type="button" className="btn-primary" onClick={() => openForm()}>Nuevo usuario</button>}
      />
      {notice && <div className="mb-3"><Alert kind="success">{notice}</Alert></div>}
      {error && !form && <div className="mb-3"><Alert>{error}</Alert></div>}

      <div className="card">
        <div className="p-4"><SearchBox value={list.search} onChange={list.setSearch} placeholder="Buscar por nombre, usuario o correo" /></div>
        {list.loading ? <Spinner /> : list.error ? <div className="p-4"><Alert>{list.error}</Alert></div> : (
          <DataTable
            rows={list.items}
            columns={[
              { header: "Usuario", render: (u) => <div><p className="font-medium">{u.full_name}</p><p className="text-xs text-slate-500">{u.username} · {u.email}</p></div> },
              { header: "Oficina principal", render: (u) => u.primary_office?.name ?? "—" },
              { header: "Visibilidad", render: (u) => <Badge tone={u.access_level === "TOTAL" ? "blue" : "slate"}>{ACCESS_LEVEL_LABEL[u.access_level]}</Badge> },
              { header: "Roles", render: (u) => <div className="flex flex-wrap gap-1">{u.roles.map((r) => <Badge key={r.id}>{r.name}</Badge>)}</div> },
              { header: "Estado", render: (u) => <Badge tone={u.is_active ? "green" : "red"}>{u.is_active ? "Activo" : "Inactivo"}</Badge> },
              ...(canManage
                ? [{
                    header: "Acciones",
                    render: (u: User) => (
                      <div className="flex flex-wrap gap-2 text-sm">
                        <button type="button" className="text-brand-700 hover:underline" onClick={() => openForm(u)}>Editar</button>
                        <button type="button" className="text-brand-700 hover:underline" onClick={() => setAssign(u)}>Oficinas</button>
                        {u.is_active && <button type="button" className="text-red-600 hover:underline" onClick={() => deactivate(u)}>Desactivar</button>}
                      </div>
                    ),
                  }]
                : []),
            ]}
          />
        )}
        <Pagination page={list.page} count={list.count} pageSize={list.pageSize} onPage={list.setPage} />
      </div>

      {form && (
        <Modal title={form.id ? "Editar usuario" : "Nuevo usuario"} onClose={() => setForm(null)} wide>
          <form onSubmit={save} className="space-y-4">
            {error && <Alert>{error}</Alert>}
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Usuario"><input className="input" required disabled={Boolean(form.id)} value={form.username} onChange={set("username")} /></Field>
              <Field label="Correo"><input className="input" type="email" required value={form.email} onChange={set("email")} /></Field>
              <Field label="Nombres"><input className="input" required value={form.first_name} onChange={set("first_name")} /></Field>
              <Field label="Apellidos"><input className="input" required value={form.last_name} onChange={set("last_name")} /></Field>
              <Field label="DNI / documento"><input className="input" value={form.document_number} onChange={set("document_number")} /></Field>
              <Field label="Teléfono"><input className="input" value={form.phone} onChange={set("phone")} /></Field>
              <Field label={form.id ? "Nueva contraseña (opcional)" : "Contraseña"} hint="Mínimo 10 caracteres; no común ni solo numérica.">
                <input className="input" type="password" autoComplete="new-password" required={!form.id} value={form.password} onChange={set("password")} />
              </Field>
              <label className="flex items-center gap-2 self-end pb-2 text-sm">
                <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Cuenta activa
              </label>
            </div>

            <fieldset className="rounded-md border border-slate-200 p-3">
              <legend className="px-1 text-sm font-medium">Roles</legend>
              <div className="grid gap-1 sm:grid-cols-2">
                {roles.map((r) => (
                  <label key={r.id} className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={form.role_ids.includes(r.id)} onChange={() => setForm({ ...form, role_ids: toggle(form.role_ids, r.id) })} /> {r.name}
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset className="rounded-md border border-slate-200 p-3">
              <legend className="px-1 text-sm font-medium">Permisos adicionales (además de los roles)</legend>
              <div className="grid max-h-44 gap-1 overflow-y-auto sm:grid-cols-2">
                {perms.map((p) => (
                  <label key={p.id} className="flex items-center gap-2 text-sm" title={p.description}>
                    <input type="checkbox" checked={form.extra_permission_ids.includes(p.id)} onChange={() => setForm({ ...form, extra_permission_ids: toggle(form.extra_permission_ids, p.id) })} />
                    {p.name}
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setForm(null)}>Cancelar</button>
              <button type="submit" className="btn-primary">Guardar</button>
            </div>
          </form>
        </Modal>
      )}

      {assign && <AssignmentsModal user={assign} onClose={() => { setAssign(null); list.reload(); }} />}
    </div>
  );
}

function AssignmentsModal({ user, onClose }: { user: User; onClose: () => void }) {
  const [items, setItems] = useState<Assignment[] | null>(null);
  const [offices, setOffices] = useState<Office[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<{ office: string; position: string; access_level: AccessLevel; is_primary: boolean; is_acting: boolean }>({
    office: "", position: "", access_level: "PERSONAL", is_primary: false, is_acting: false,
  });

  const load = () =>
    Promise.all([
      assignmentsApi.list({ user: user.id, is_active: true, page_size: 100 }),
      officesApi.list({ is_active: true, page_size: 100 }),
      positionsApi.list({ page_size: 100 }),
    ])
      .then(([a, o, p]) => { setItems(a.results); setOffices(o.results); setPositions(p.results.filter((x) => x.is_active)); })
      .catch((e) => setError(errorMessage(e)));

  useState(() => { load(); });

  const add = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await assignmentsApi.create({
        user: user.id,
        office: Number(draft.office),
        position: draft.position ? Number(draft.position) : null,
        access_level: draft.access_level,
        is_primary: draft.is_primary,
        is_acting: draft.is_acting,
      });
      setDraft({ ...draft, office: "", position: "", is_primary: false, is_acting: false });
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const changeLevel = async (a: Assignment, level: AccessLevel) => {
    try {
      await assignmentsApi.update(a.id, { access_level: level });
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const end = async (a: Assignment) => {
    if (!window.confirm(`¿Finalizar la asignación en ${a.office_name}?`)) return;
    try {
      await assignmentsApi.remove(a.id);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <Modal title={`Oficinas de ${user.full_name}`} onClose={onClose} wide>
      <div className="space-y-4">
        {error && <Alert>{error}</Alert>}
        <Alert kind="info">El acceso total permite ver los documentos de la oficina; no concede permiso de firmar, aprobar, emitir ni anular.</Alert>
        {!items ? <Spinner /> : (
          <DataTable
            rows={items}
            empty="Sin asignaciones vigentes."
            columns={[
              { header: "Oficina", render: (a) => <>{a.office_name} {a.is_primary && <Badge tone="green">Principal</Badge>}</> },
              { header: "Cargo", render: (a) => a.position_name ?? "—" },
              {
                header: "Visibilidad",
                render: (a) => (
                  <select className="input py-1" value={a.access_level} onChange={(e) => changeLevel(a, e.target.value as AccessLevel)}>
                    <option value="PERSONAL">{ACCESS_LEVEL_LABEL.PERSONAL}</option>
                    <option value="TOTAL">{ACCESS_LEVEL_LABEL.TOTAL}</option>
                  </select>
                ),
              },
              { header: "", render: (a) => <button type="button" className="text-sm text-red-600 hover:underline" onClick={() => end(a)}>Finalizar</button> },
            ]}
          />
        )}
        <form onSubmit={add} className="grid gap-3 rounded-md border border-slate-200 p-3 sm:grid-cols-2">
          <Field label="Oficina">
            <select className="input" required value={draft.office} onChange={(e) => setDraft({ ...draft, office: e.target.value })}>
              <option value="">Seleccione…</option>
              {offices.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
          </Field>
          <Field label="Cargo">
            <select className="input" value={draft.position} onChange={(e) => setDraft({ ...draft, position: e.target.value })}>
              <option value="">—</option>
              {positions.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
          <Field label="Nivel de visibilidad">
            <select className="input" value={draft.access_level} onChange={(e) => setDraft({ ...draft, access_level: e.target.value as AccessLevel })}>
              <option value="PERSONAL">{ACCESS_LEVEL_LABEL.PERSONAL}</option>
              <option value="TOTAL">{ACCESS_LEVEL_LABEL.TOTAL}</option>
            </select>
          </Field>
          <div className="flex flex-col justify-end gap-1 text-sm">
            <label className="flex items-center gap-2"><input type="checkbox" checked={draft.is_primary} onChange={(e) => setDraft({ ...draft, is_primary: e.target.checked })} /> Oficina principal</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={draft.is_acting} onChange={(e) => setDraft({ ...draft, is_acting: e.target.checked })} /> Encargatura</label>
          </div>
          <div className="sm:col-span-2 flex justify-end"><button type="submit" className="btn-primary">Agregar asignación</button></div>
        </form>
      </div>
    </Modal>
  );
}

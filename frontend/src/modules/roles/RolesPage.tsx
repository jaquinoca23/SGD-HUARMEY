import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "../../app/AuthContext";
import { Alert, Badge, DataTable, Field, Modal, PageHeader, Spinner } from "../../components/ui";
import { permissionsApi, rolesApi } from "../../services/api";
import { errorMessage } from "../../services/http";
import type { AppPermission, Role } from "../../types";

export function RolesPage() {
  const { can } = useAuth();
  const canManage = can("roles.manage");
  const [roles, setRoles] = useState<Role[] | null>(null);
  const [perms, setPerms] = useState<AppPermission[]>([]);
  const [editing, setEditing] = useState<Partial<Role> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = () =>
    Promise.all([rolesApi.list({ page_size: 100 }), permissionsApi.list()])
      .then(([r, p]) => { setRoles(r.results); setPerms(p); })
      .catch((e) => setError(errorMessage(e)));

  useEffect(() => { load(); }, []);

  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    setError(null);
    const body = { code: editing.code, name: editing.name, description: editing.description ?? "", permission_ids: editing.permission_ids ?? [], is_active: editing.is_active ?? true };
    try {
      if (editing.id) await rolesApi.update(editing.id, body);
      else await rolesApi.create(body);
      setEditing(null);
      setNotice("Rol guardado.");
      load();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const togglePerm = (id: number) => {
    const current = editing?.permission_ids ?? [];
    setEditing({ ...editing, permission_ids: current.includes(id) ? current.filter((x) => x !== id) : [...current, id] });
  };

  const categories = [
    { key: "ADMINISTRATION", label: "Administración" },
    { key: "OPERATIONAL", label: "Operativos" },
    { key: "SIGNATURE", label: "Firma y emisión (reservados: se aplicarán en fases posteriores)" },
  ] as const;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Roles y permisos"
        subtitle="Los permisos operativos y de firma son independientes del nivel de acceso (personal / total)."
        actions={canManage && <button type="button" className="btn-primary" onClick={() => { setError(null); setEditing({ permission_ids: [], is_active: true }); }}>Nuevo rol</button>}
      />
      {notice && <Alert kind="success">{notice}</Alert>}
      {error && !editing && <Alert>{error}</Alert>}

      <div className="card">
        {!roles ? <Spinner /> : (
          <DataTable
            rows={roles}
            columns={[
              { header: "Rol", render: (r) => <div><p className="font-medium">{r.name}</p><p className="text-xs text-slate-500">{r.description}</p></div> },
              { header: "Código", render: (r) => <code className="text-xs">{r.code}</code> },
              { header: "Permisos", render: (r) => <span className="text-xs text-slate-600">{r.permission_codes.length}</span> },
              { header: "Usuarios", render: (r) => r.users_count },
              { header: "Estado", render: (r) => <>{r.is_system && <Badge tone="blue">Sistema</Badge>} <Badge tone={r.is_active ? "green" : "red"}>{r.is_active ? "Activo" : "Inactivo"}</Badge></> },
              ...(canManage ? [{ header: "", render: (r: Role) => <button type="button" className="text-sm text-brand-700 hover:underline" onClick={() => { setError(null); setEditing(r); }}>Editar</button> }] : []),
            ]}
          />
        )}
      </div>

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-semibold">Catálogo de permisos</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {categories.map((c) => (
            <div key={c.key}>
              <h3 className="mb-1 text-xs font-semibold uppercase text-slate-500">{c.label}</h3>
              <ul className="space-y-1 text-sm">
                {perms.filter((p) => p.category === c.key).map((p) => (
                  <li key={p.id}><code className="text-xs">{p.code}</code><span className="block text-xs text-slate-500">{p.name}</span></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {editing && (
        <Modal title={editing.id ? "Editar rol" : "Nuevo rol"} onClose={() => setEditing(null)} wide>
          <form onSubmit={save} className="space-y-4">
            {error && <Alert>{error}</Alert>}
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Código"><input className="input" required disabled={editing.is_system} value={editing.code ?? ""} onChange={(e) => setEditing({ ...editing, code: e.target.value })} /></Field>
              <Field label="Nombre"><input className="input" required value={editing.name ?? ""} onChange={(e) => setEditing({ ...editing, name: e.target.value })} /></Field>
            </div>
            <Field label="Descripción"><input className="input" value={editing.description ?? ""} onChange={(e) => setEditing({ ...editing, description: e.target.value })} /></Field>
            {categories.map((c) => (
              <fieldset key={c.key} className="rounded-md border border-slate-200 p-3">
                <legend className="px-1 text-sm font-medium">{c.label}</legend>
                <div className="grid gap-1 sm:grid-cols-2">
                  {perms.filter((p) => p.category === c.key).map((p) => (
                    <label key={p.id} className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={(editing.permission_ids ?? []).includes(p.id)} onChange={() => togglePerm(p.id)} /> {p.name}
                    </label>
                  ))}
                </div>
              </fieldset>
            ))}
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={editing.is_active ?? true} onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> Rol activo</label>
            <div className="flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setEditing(null)}>Cancelar</button>
              <button type="submit" className="btn-primary">Guardar</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

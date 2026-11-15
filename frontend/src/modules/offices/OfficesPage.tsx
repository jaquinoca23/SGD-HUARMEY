import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "../../app/AuthContext";
import { useList } from "../../app/useList";
import { Alert, Badge, DataTable, Field, Modal, PageHeader, Pagination, SearchBox, Spinner } from "../../components/ui";
import { officesApi } from "../../services/api";
import { errorMessage } from "../../services/http";
import type { Office, OfficeKind, OfficeNode } from "../../types";

const KINDS: { value: OfficeKind; label: string }[] = [
  { value: "GOVERNING", label: "Órgano de gobierno y dirección" },
  { value: "GENERAL", label: "Oficina general" },
  { value: "MANAGEMENT", label: "Gerencia" },
  { value: "UNIT", label: "Subgerencia / unidad" },
  { value: "OTHER", label: "Otro órgano" },
];

function Tree({ nodes, depth = 0 }: { nodes: OfficeNode[]; depth?: number }) {
  return (
    <ul className={depth ? "ml-5 border-l border-slate-200 pl-3" : ""}>
      {nodes.map((n) => (
        <li key={n.id} className="py-0.5">
          <span className="text-sm">{n.name}</span> <span className="text-xs text-slate-400">{n.code}</span>
          {n.children.length > 0 && <Tree nodes={n.children} depth={depth + 1} />}
        </li>
      ))}
    </ul>
  );
}

export function OfficesPage() {
  const { can } = useAuth();
  const canManage = can("offices.manage");
  const list = useList<Office>(officesApi.list);
  const [view, setView] = useState<"table" | "tree">("table");
  const [tree, setTree] = useState<OfficeNode[] | null>(null);
  const [editing, setEditing] = useState<Partial<Office> | null>(null);
  const [parents, setParents] = useState<Office[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (view === "tree") officesApi.tree().then(setTree).catch((e) => setError(errorMessage(e)));
  }, [view, list.items]);

  const openForm = async (office: Partial<Office>) => {
    setError(null);
    try {
      setParents((await officesApi.list({ page_size: 100, is_active: true, ordering: "name" })).results);
      setEditing(office);
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    setError(null);
    const body = {
      code: editing.code,
      name: editing.name,
      kind: editing.kind ?? "UNIT",
      parent: editing.parent ?? null,
      is_active: editing.is_active ?? true,
    };
    try {
      if (editing.id) await officesApi.update(editing.id, body);
      else await officesApi.create(body);
      setEditing(null);
      setNotice("Oficina guardada.");
      list.reload();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const deactivate = async (office: Office) => {
    if (!window.confirm(`¿Desactivar «${office.name}»?`)) return;
    try {
      await officesApi.remove(office.id);
      setNotice("Oficina desactivada.");
      list.reload();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div>
      <PageHeader
        title="Oficinas y dependencias"
        subtitle="Estructura jerárquica base. Debe ajustarse al ROF vigente."
        actions={
          <>
            <button type="button" className="btn-secondary" onClick={() => setView(view === "table" ? "tree" : "table")}>
              {view === "table" ? "Ver jerarquía" : "Ver tabla"}
            </button>
            {canManage && <button type="button" className="btn-primary" onClick={() => openForm({ kind: "UNIT", is_active: true })}>Nueva oficina</button>}
          </>
        }
      />
      {notice && <div className="mb-3"><Alert kind="success">{notice}</Alert></div>}
      {error && !editing && <div className="mb-3"><Alert>{error}</Alert></div>}

      {view === "tree" ? (
        <div className="card p-4">{tree ? <Tree nodes={tree} /> : <Spinner />}</div>
      ) : (
        <div className="card">
          <div className="p-4"><SearchBox value={list.search} onChange={list.setSearch} placeholder="Buscar por nombre o código" /></div>
          {list.loading ? <Spinner /> : list.error ? <div className="p-4"><Alert>{list.error}</Alert></div> : (
            <DataTable
              rows={list.items}
              columns={[
                { header: "Código", render: (o) => <code className="text-xs">{o.code}</code> },
                { header: "Nombre", render: (o) => o.name },
                { header: "Tipo", render: (o) => o.kind_display },
                { header: "Depende de", render: (o) => o.parent_name ?? "—" },
                { header: "Estado", render: (o) => <Badge tone={o.is_active ? "green" : "red"}>{o.is_active ? "Activa" : "Inactiva"}</Badge> },
                ...(canManage
                  ? [{
                      header: "Acciones",
                      render: (o: Office) => (
                        <div className="flex gap-2">
                          <button type="button" className="text-sm text-brand-700 hover:underline" onClick={() => openForm(o)}>Editar</button>
                          {o.is_active && <button type="button" className="text-sm text-red-600 hover:underline" onClick={() => deactivate(o)}>Desactivar</button>}
                        </div>
                      ),
                    }]
                  : []),
              ]}
            />
          )}
          <Pagination page={list.page} count={list.count} pageSize={list.pageSize} onPage={list.setPage} />
        </div>
      )}

      {editing && (
        <Modal title={editing.id ? "Editar oficina" : "Nueva oficina"} onClose={() => setEditing(null)}>
          <form onSubmit={save} className="space-y-4">
            {error && <Alert>{error}</Alert>}
            <Field label="Código"><input className="input" required maxLength={30} value={editing.code ?? ""} onChange={(e) => setEditing({ ...editing, code: e.target.value })} /></Field>
            <Field label="Nombre"><input className="input" required maxLength={200} value={editing.name ?? ""} onChange={(e) => setEditing({ ...editing, name: e.target.value })} /></Field>
            <Field label="Tipo">
              <select className="input" value={editing.kind ?? "UNIT"} onChange={(e) => setEditing({ ...editing, kind: e.target.value as OfficeKind })}>
                {KINDS.map((k) => <option key={k.value} value={k.value}>{k.label}</option>)}
              </select>
            </Field>
            <Field label="Depende de">
              <select className="input" value={editing.parent ?? ""} onChange={(e) => setEditing({ ...editing, parent: e.target.value ? Number(e.target.value) : null })}>
                <option value="">— Ninguna (nivel superior) —</option>
                {parents.filter((p) => p.id !== editing.id).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </Field>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={editing.is_active ?? true} onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> Activa
            </label>
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

import { FormEvent, useState } from "react";

import { useAuth } from "../../app/AuthContext";
import { useList } from "../../app/useList";
import { Alert, Badge, DataTable, Field, Modal, PageHeader, Pagination, SearchBox, Spinner } from "../../components/ui";
import { documentTypesApi, templatesApi } from "../../services/api";
import { errorMessage } from "../../services/http";
import type { DocumentType, IssuanceScope, Template } from "../../types";

const SCOPES: { value: IssuanceScope; label: string }[] = [
  { value: "OFFICE", label: "Dentro de la misma oficina" },
  { value: "INTERNAL", label: "Entre oficinas de la municipalidad" },
  { value: "EXTERNAL", label: "Hacia el exterior" },
  { value: "NORMATIVE", label: "Normativo / órgano de gobierno" },
];

export function DocumentTypesPage() {
  const { can } = useAuth();
  const canManage = can("document_types.manage");
  const list = useList<DocumentType>(documentTypesApi.list, {}, 12);
  const [editing, setEditing] = useState<Partial<DocumentType> | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const openForm = async (item: Partial<DocumentType>) => {
    setError(null);
    try {
      setTemplates(item.id ? (await templatesApi.list({ document_type: item.id, page_size: 100 })).results : []);
      setEditing(item);
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
      description: editing.description ?? "",
      requires_signature: editing.requires_signature ?? true,
      issuance_scope: editing.issuance_scope ?? "INTERNAL",
      allows_multiple_recipients: editing.allows_multiple_recipients ?? false,
      default_template: editing.default_template ?? null,
      is_active: editing.is_active ?? true,
    };
    try {
      if (editing.id) await documentTypesApi.update(editing.id, body);
      else await documentTypesApi.create({ ...body, default_template: null });
      setEditing(null);
      setNotice("Tipo documental guardado.");
      list.reload();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div>
      <PageHeader
        title="Tipos documentales"
        subtitle="Catálogo inicial. Los valores de firma y ámbito son una propuesta que Secretaría General debe validar."
        actions={canManage && <button type="button" className="btn-primary" onClick={() => openForm({ requires_signature: true, issuance_scope: "INTERNAL", allows_multiple_recipients: false, is_active: true })}>Nuevo tipo</button>}
      />
      {notice && <div className="mb-3"><Alert kind="success">{notice}</Alert></div>}
      {error && !editing && <div className="mb-3"><Alert>{error}</Alert></div>}

      <div className="card">
        <div className="p-4"><SearchBox value={list.search} onChange={list.setSearch} placeholder="Buscar tipo documental" /></div>
        {list.loading ? <Spinner /> : list.error ? <div className="p-4"><Alert>{list.error}</Alert></div> : (
          <DataTable
            rows={list.items}
            columns={[
              { header: "Tipo", render: (t) => <div><p className="font-medium">{t.name}</p><code className="text-xs text-slate-500">{t.code}</code></div> },
              { header: "Firma", render: (t) => <Badge tone={t.requires_signature ? "amber" : "slate"}>{t.requires_signature ? "Requiere" : "No requiere"}</Badge> },
              { header: "Ámbito", render: (t) => t.issuance_scope_display },
              { header: "Dest. múltiples", render: (t) => (t.allows_multiple_recipients ? "Sí" : "No") },
              { header: "Plantilla predeterminada", render: (t) => t.default_template_name ?? "—" },
              { header: "Estado", render: (t) => <Badge tone={t.is_active ? "green" : "red"}>{t.is_active ? "Activo" : "Inactivo"}</Badge> },
              ...(canManage ? [{ header: "", render: (t: DocumentType) => <button type="button" className="text-sm text-brand-700 hover:underline" onClick={() => openForm(t)}>Editar</button> }] : []),
            ]}
          />
        )}
        <Pagination page={list.page} count={list.count} pageSize={list.pageSize} onPage={list.setPage} />
      </div>

      {editing && (
        <Modal title={editing.id ? "Editar tipo documental" : "Nuevo tipo documental"} onClose={() => setEditing(null)}>
          <form onSubmit={save} className="space-y-4">
            {error && <Alert>{error}</Alert>}
            <Field label="Código"><input className="input" required value={editing.code ?? ""} onChange={(e) => setEditing({ ...editing, code: e.target.value })} /></Field>
            <Field label="Nombre"><input className="input" required value={editing.name ?? ""} onChange={(e) => setEditing({ ...editing, name: e.target.value })} /></Field>
            <Field label="Descripción"><input className="input" value={editing.description ?? ""} onChange={(e) => setEditing({ ...editing, description: e.target.value })} /></Field>
            <Field label="Ámbito de emisión">
              <select className="input" value={editing.issuance_scope ?? "INTERNAL"} onChange={(e) => setEditing({ ...editing, issuance_scope: e.target.value as IssuanceScope })}>
                {SCOPES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </Field>
            {editing.id && (
              <Field label="Plantilla predeterminada" hint="Solo plantillas activas de este tipo.">
                <select className="input" value={editing.default_template ?? ""} onChange={(e) => setEditing({ ...editing, default_template: e.target.value ? Number(e.target.value) : null })}>
                  <option value="">— Ninguna —</option>
                  {templates.filter((t) => t.is_active).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </Field>
            )}
            <div className="space-y-1 text-sm">
              <label className="flex items-center gap-2"><input type="checkbox" checked={editing.requires_signature ?? true} onChange={(e) => setEditing({ ...editing, requires_signature: e.target.checked })} /> Requiere firma</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={editing.allows_multiple_recipients ?? false} onChange={(e) => setEditing({ ...editing, allows_multiple_recipients: e.target.checked })} /> Permite destinatarios múltiples</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={editing.is_active ?? true} onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> Activo</label>
            </div>
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

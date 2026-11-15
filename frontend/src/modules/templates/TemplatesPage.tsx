import { FormEvent, useState } from "react";

import { useAuth } from "../../app/AuthContext";
import { useList } from "../../app/useList";
import { Alert, Badge, DataTable, Field, Modal, PageHeader, Pagination, SearchBox, Spinner } from "../../components/ui";
import { documentTypesApi, officesApi, templatesApi } from "../../services/api";
import { errorMessage } from "../../services/http";
import type { DocumentType, Office, Template, TemplateVersion } from "../../types";

const MAX_MB = 5;

function formatSize(bytes: number) {
  return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

export function TemplatesPage() {
  const { can } = useAuth();
  const canManage = can("templates.manage");
  const list = useList<Template>(templatesApi.list);
  const [editing, setEditing] = useState<Partial<Template> | null>(null);
  const [types, setTypes] = useState<DocumentType[]>([]);
  const [offices, setOffices] = useState<Office[]>([]);
  const [versionsOf, setVersionsOf] = useState<Template | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const openForm = async (item: Partial<Template>) => {
    setError(null);
    try {
      const [t, o] = await Promise.all([
        documentTypesApi.list({ page_size: 100 }),
        officesApi.list({ page_size: 100, is_active: true }),
      ]);
      setTypes(t.results.filter((x) => x.is_active));
      setOffices(o.results);
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
      name: editing.name,
      description: editing.description ?? "",
      document_type: editing.document_type,
      office: editing.office ?? null,
      is_private: editing.is_private ?? false,
      is_active: editing.is_active ?? true,
    };
    try {
      if (editing.id) await templatesApi.update(editing.id, body);
      else await templatesApi.create(body);
      setEditing(null);
      setNotice("Plantilla guardada. Suba el archivo DOCX desde «Versiones».");
      list.reload();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div>
      <PageHeader
        title="Plantillas documentales"
        subtitle="Catálogo de plantillas DOCX con versiones. Las plantillas privadas solo son visibles para la oficina indicada."
        actions={canManage && <button type="button" className="btn-primary" onClick={() => openForm({ is_active: true, is_private: false })}>Nueva plantilla</button>}
      />
      {notice && <div className="mb-3"><Alert kind="success">{notice}</Alert></div>}
      {error && !editing && <div className="mb-3"><Alert>{error}</Alert></div>}

      <div className="card">
        <div className="p-4"><SearchBox value={list.search} onChange={list.setSearch} placeholder="Buscar plantilla, tipo u oficina" /></div>
        {list.loading ? <Spinner /> : list.error ? <div className="p-4"><Alert>{list.error}</Alert></div> : (
          <DataTable
            rows={list.items}
            empty="No hay plantillas registradas."
            columns={[
              { header: "Plantilla", render: (t) => <div><p className="font-medium">{t.name}</p><p className="text-xs text-slate-500">{t.document_type_name}</p></div> },
              { header: "Oficina", render: (t) => t.office_name ?? "General" },
              {
                header: "Versión vigente",
                render: (t) =>
                  t.current_version_detail ? (
                    <div className="space-y-1">
                      <span>v{t.current_version_detail.version_number}{t.current_version_detail.version_label ? ` (${t.current_version_detail.version_label})` : ""}</span>{" "}
                      {!t.current_version_detail.is_official && <Badge tone="amber">NO oficial</Badge>}
                    </div>
                  ) : <span className="text-slate-400">Sin archivo</span>,
              },
              { header: "Alcance", render: (t) => <Badge tone={t.is_private ? "blue" : "slate"}>{t.is_private ? "Privada" : "Pública"}</Badge> },
              { header: "Estado", render: (t) => <Badge tone={t.is_active ? "green" : "red"}>{t.is_active ? "Activa" : "Inactiva"}</Badge> },
              {
                header: "Acciones",
                render: (t) => (
                  <div className="flex gap-3 text-sm">
                    <button type="button" className="text-brand-700 hover:underline" onClick={() => setVersionsOf(t)}>Versiones ({t.versions_count})</button>
                    {canManage && <button type="button" className="text-brand-700 hover:underline" onClick={() => openForm(t)}>Editar</button>}
                  </div>
                ),
              },
            ]}
          />
        )}
        <Pagination page={list.page} count={list.count} pageSize={list.pageSize} onPage={list.setPage} />
      </div>

      {editing && (
        <Modal title={editing.id ? "Editar plantilla" : "Nueva plantilla"} onClose={() => setEditing(null)}>
          <form onSubmit={save} className="space-y-4">
            {error && <Alert>{error}</Alert>}
            <Field label="Nombre"><input className="input" required value={editing.name ?? ""} onChange={(e) => setEditing({ ...editing, name: e.target.value })} /></Field>
            <Field label="Descripción"><input className="input" value={editing.description ?? ""} onChange={(e) => setEditing({ ...editing, description: e.target.value })} /></Field>
            <Field label="Tipo documental">
              <select className="input" required value={editing.document_type ?? ""} onChange={(e) => setEditing({ ...editing, document_type: Number(e.target.value) })}>
                <option value="">Seleccione…</option>
                {types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </Field>
            <Field label="Oficina" hint="Vacío = plantilla general para todas las oficinas.">
              <select className="input" value={editing.office ?? ""} onChange={(e) => setEditing({ ...editing, office: e.target.value ? Number(e.target.value) : null })}>
                <option value="">— General —</option>
                {offices.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
              </select>
            </Field>
            <div className="space-y-1 text-sm">
              <label className="flex items-center gap-2"><input type="checkbox" checked={editing.is_private ?? false} onChange={(e) => setEditing({ ...editing, is_private: e.target.checked })} /> Privada (solo la oficina indicada)</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={editing.is_active ?? true} onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> Activa</label>
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setEditing(null)}>Cancelar</button>
              <button type="submit" className="btn-primary">Guardar</button>
            </div>
          </form>
        </Modal>
      )}

      {versionsOf && <VersionsModal template={versionsOf} canManage={canManage} onClose={() => { setVersionsOf(null); list.reload(); }} />}
    </div>
  );
}

function VersionsModal({ template, canManage, onClose }: { template: Template; canManage: boolean; onClose: () => void }) {
  const [versions, setVersions] = useState<TemplateVersion[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [label, setLabel] = useState("");
  const [notes, setNotes] = useState("");
  const [official, setOfficial] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = () => templatesApi.versions(template.id).then(setVersions).catch((e) => setError(errorMessage(e)));
  useState(() => { load(); });

  const pickFile = (f: File | null) => {
    setError(null);
    if (f && !f.name.toLowerCase().endsWith(".docx")) { setError("Solo se permiten archivos .docx."); setFile(null); return; }
    if (f && f.size > MAX_MB * 1024 * 1024) { setError(`El archivo supera ${MAX_MB} MB.`); setFile(null); return; }
    setFile(f);
  };

  const upload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    form.append("version_label", label);
    form.append("notes", notes);
    form.append("is_official", String(official));
    try {
      await templatesApi.uploadVersion(template.id, form);
      setFile(null); setLabel(""); setNotes(""); setOfficial(false);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const makeCurrent = async (v: TemplateVersion) => {
    try { await templatesApi.setCurrent(template.id, v.id); await load(); } catch (err) { setError(errorMessage(err)); }
  };

  const download = async (v: TemplateVersion) => {
    try { await templatesApi.download(v); } catch (err) { setError(errorMessage(err)); }
  };

  return (
    <Modal title={`Versiones: ${template.name}`} onClose={onClose} wide>
      <div className="space-y-4">
        {error && <Alert>{error}</Alert>}
        {!versions ? <Spinner /> : (
          <DataTable
            rows={versions}
            empty="Aún no hay versiones. Suba el primer archivo DOCX."
            columns={[
              { header: "Versión", render: (v) => <>v{v.version_number} {v.version_label && `(${v.version_label})`} {v.is_current && <Badge tone="green">Vigente</Badge>}</> },
              { header: "Archivo", render: (v) => <div><p>{v.file_name}</p><p className="text-xs text-slate-500">{formatSize(v.file_size)} · SHA-256 {v.checksum_sha256.slice(0, 12)}…</p></div> },
              { header: "Origen", render: (v) => (v.is_official ? <Badge tone="green">Oficial</Badge> : <Badge tone="amber">NO oficial / demo</Badge>) },
              { header: "Fecha", render: (v) => new Date(v.created_at).toLocaleDateString("es-PE") },
              {
                header: "",
                render: (v) => (
                  <div className="flex gap-3 text-sm">
                    <button type="button" className="text-brand-700 hover:underline" onClick={() => download(v)}>Descargar</button>
                    {canManage && !v.is_current && <button type="button" className="text-brand-700 hover:underline" onClick={() => makeCurrent(v)}>Hacer vigente</button>}
                  </div>
                ),
              },
            ]}
          />
        )}
        {canManage && (
          <form onSubmit={upload} className="space-y-3 rounded-md border border-slate-200 p-3">
            <h3 className="text-sm font-semibold">Subir nueva versión (se convierte en la vigente)</h3>
            <Field label={`Archivo DOCX (máx. ${MAX_MB} MB)`}>
              <input className="input" type="file" accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(e) => pickFile(e.target.files?.[0] ?? null)} />
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Etiqueta de versión"><input className="input" maxLength={50} value={label} onChange={(e) => setLabel(e.target.value)} /></Field>
              <Field label="Notas"><input className="input" maxLength={500} value={notes} onChange={(e) => setNotes(e.target.value)} /></Field>
            </div>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={official} onChange={(e) => setOfficial(e.target.checked)} /> Marcar como plantilla oficial aprobada por la entidad</label>
            <button type="submit" className="btn-primary" disabled={!file || busy}>{busy ? "Subiendo…" : "Subir versión"}</button>
          </form>
        )}
      </div>
    </Modal>
  );
}

import { FormEvent, useEffect, useState } from "react";

import { Alert, Badge, DataTable, Field, PageHeader, Spinner } from "../components/ui";
import { documentTypesApi, draftsApi } from "../services/api";
import { errorMessage } from "../services/http";
import type { DocumentDraft, DocumentType } from "../types";

export function NewDocumentPage() {
  const [types, setTypes] = useState<DocumentType[]>([]);
  const [recent, setRecent] = useState<DocumentDraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeId, setTypeId] = useState("");
  const [title, setTitle] = useState("");
  const [confidential, setConfidential] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<DocumentDraft | null>(null);
  const [busy, setBusy] = useState(false);

  const loadRecent = () => draftsApi.list({ scope: "mine", page_size: 5 }).then((d) => setRecent(d.results));

  useEffect(() => {
    Promise.all([documentTypesApi.list({ page_size: 100, is_active: true }), loadRecent()])
      .then(([t]) => setTypes(t.results.filter((x) => x.is_active)))
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  const selected = types.find((t) => String(t.id) === typeId);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setCreated(null);
    try {
      const draft = await draftsApi.create({
        document_type: Number(typeId),
        title,
        confidentiality: confidential ? "CONFIDENTIAL" : "NORMAL",
      });
      setCreated(draft);
      setTitle("");
      await loadRecent();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="space-y-6">
      <PageHeader title="Nuevo documento" subtitle="Registre un borrador a partir de un tipo documental. La plantilla vigente se asigna automáticamente." />

      <Alert kind="warning">
        En la Fase 01 solo se registra el borrador en el sistema. La creación del archivo en la carpeta «H Documentos», su apertura en Word y la
        edición sin conexión corresponden a SGDGuarmail, que aún no está implementado.
      </Alert>

      <form onSubmit={submit} className="card max-w-2xl space-y-4 p-5">
        {error && <Alert>{error}</Alert>}
        <Field label="Tipo documental">
          <select className="input" required value={typeId} onChange={(e) => setTypeId(e.target.value)}>
            <option value="">Seleccione…</option>
            {types.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </Field>
        {selected && (
          <div className="flex flex-wrap gap-2 text-xs">
            <Badge tone={selected.requires_signature ? "amber" : "slate"}>{selected.requires_signature ? "Requiere firma" : "Sin firma"}</Badge>
            <Badge tone="blue">{selected.issuance_scope_display}</Badge>
            {selected.allows_multiple_recipients && <Badge>Destinatarios múltiples</Badge>}
          </div>
        )}
        <Field label="Asunto / título">
          <input className="input" required maxLength={250} value={title} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={confidential} onChange={(e) => setConfidential(e.target.checked)} />
          Marcar como confidencial (solo usted y la persona asignada lo verán)
        </label>
        <button type="submit" className="btn-primary" disabled={busy || !typeId}>
          {busy ? "Registrando…" : "Registrar borrador"}
        </button>
      </form>

      {created && (
        <Alert kind="success">
          Borrador «{created.title}» registrado en {created.office_name}.{" "}
          {created.template_resolved
            ? `Plantilla: ${created.template_name} (v${created.template_version_number}${created.template_is_official === false ? ", NO oficial" : ""}).`
            : "No hay una plantilla vigente para este tipo; solicítela a Secretaría General."}
        </Alert>
      )}

      <section className="card">
        <h2 className="border-b border-slate-200 px-4 py-3 text-sm font-semibold">Mis últimos borradores</h2>
        <DataTable
          rows={recent}
          empty="Aún no ha registrado borradores."
          columns={[
            { header: "Asunto", render: (d) => d.title },
            { header: "Tipo", render: (d) => d.document_type_name },
            { header: "Oficina", render: (d) => d.office_name },
            { header: "Plantilla", render: (d) => (d.template_resolved ? `${d.template_name} v${d.template_version_number}` : "—") },
            { header: "Fecha", render: (d) => new Date(d.created_at).toLocaleString("es-PE") },
          ]}
        />
      </section>
    </div>
  );
}

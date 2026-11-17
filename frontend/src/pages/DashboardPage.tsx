import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Banner } from "../components/Banner";
import { Alert, Spinner } from "../components/ui";
import { dashboardApi } from "../services/api";
import { errorMessage } from "../services/http";
import type { DashboardItem, DashboardSummary } from "../types";

function Counter({ value, available }: { value: number | null; available: boolean }) {
  return (
    <span
      className={`inline-flex min-w-9 items-center justify-center rounded-lg px-2 py-0.5 text-lg font-bold text-white ${available ? "bg-slate-700" : "bg-slate-300"}`}
      title={available ? undefined : "Se activará con el flujo documental (Fase 2)"}
      aria-label={available ? `${value} documentos` : "No disponible todavía"}
    >
      {available ? value : "—"}
    </span>
  );
}

function Row({ item }: { item: DashboardItem }) {
  const body = (
    <div className={`flex items-start justify-between gap-3 px-5 py-3 ${item.indent ? "ml-8 border-l border-slate-200" : ""}`}>
      <div>
        <p className={`font-bold uppercase text-slate-800 ${item.indent ? "text-base" : "text-lg"}`}>{item.label}</p>
        <p className="text-sm text-sky-700">{item.description}</p>
        {!item.available && <p className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">Disponible en la Fase 2</p>}
      </div>
      <Counter value={item.value} available={item.available} />
    </div>
  );
  return item.link && item.available ? (
    <Link to={item.link} className="block hover:bg-slate-50">{body}</Link>
  ) : (
    <div>{body}</div>
  );
}

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    dashboardApi
      .summary()
      .then((data) => { setSummary(data); setError(null); })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  return (
    <div className="grid items-start gap-5 lg:grid-cols-[minmax(300px,380px)_1fr]">
      <section className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm" aria-label="Resumen de documentos">
        <div className="bg-sky-600 px-5 py-3 text-white">
          <div className="flex items-center justify-between gap-2">
            <h1 className="text-xl font-bold">{summary?.title ?? "Mis documentos"}</h1>
            <button type="button" onClick={load} className="rounded p-1 text-xl hover:bg-sky-700" aria-label="Actualizar resumen" title="Actualizar">
              ⟳
            </button>
          </div>
          <p className="text-sm">{summary?.subtitle ?? "Resumen de los documentos principales"}</p>
        </div>

        {loading && !summary ? (
          <Spinner />
        ) : error ? (
          <div className="p-4"><Alert>{error}</Alert></div>
        ) : (
          <div className="divide-y divide-slate-200">
            {summary?.items.map((item) => <Row key={item.key} item={item} />)}
          </div>
        )}
      </section>

      <Banner />
    </div>
  );
}

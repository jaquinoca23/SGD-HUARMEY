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
      className={`inline-flex min-w-11 items-center justify-center rounded-xl px-3 py-2 text-lg font-bold tabular-nums ${available ? "bg-brand-50 text-brand-800" : "bg-slate-100 text-slate-400"}`}
      title={available ? undefined : "Se activará con el flujo documental (Fase 2)"}
      aria-label={available ? `${value} documentos` : "No disponible todavía"}
    >
      {available ? value : "—"}
    </span>
  );
}

function Row({ item }: { item: DashboardItem }) {
  const body = (
    <div className={`flex items-center justify-between gap-4 rounded-xl px-4 py-3 transition-colors ${item.indent ? "ml-5 border-l-2 border-brand-100 pl-5" : ""} ${item.link && item.available ? "hover:bg-slate-50" : ""}`}>
      <div className="min-w-0">
        <p className={`font-semibold text-slate-800 ${item.indent ? "text-sm" : "text-[15px]"}`}>{item.label}</p>
        <p className="mt-0.5 text-sm leading-relaxed text-slate-500">{item.description}</p>
        {!item.available && <p className="mt-1 text-[11px] font-medium uppercase tracking-wide text-slate-400">Disponible en la Fase 2</p>}
      </div>
      <Counter value={item.value} available={item.available} />
    </div>
  );
  return item.link && item.available ? (
    <Link to={item.link} className="block rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500">{body}</Link>
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
    <div className="mx-auto max-w-[1440px] space-y-6">
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-900 via-brand-800 to-teal-800 px-6 py-7 text-white shadow-sm sm:px-9 sm:py-9">
        <div className="pointer-events-none absolute -right-12 -top-24 h-72 w-72 rounded-full border border-white/10" />
        <div className="pointer-events-none absolute -right-2 -top-14 h-52 w-52 rounded-full border border-white/10" />
        <div className="relative max-w-2xl">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-teal-200">HUARMY · GESTIÓN DOCUMENTAL</p>
          <h1 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">Tu espacio de trabajo</h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-teal-50/85 sm:text-base">
            Consulta el resumen de tu actividad y accede a la información de tu oficina desde un solo lugar.
          </p>
        </div>
      </section>

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(340px,0.85fr)_minmax(0,1.5fr)]">
        <section className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm" aria-label="Resumen de documentos">
          <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-5 sm:px-6">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.15em] text-brand-600">Resumen</p>
              <h2 className="mt-1 text-lg font-bold tracking-tight text-slate-900">{summary?.title ?? "Mis documentos"}</h2>
              <p className="mt-1 text-sm text-slate-500">{summary?.subtitle ?? "Resumen de los documentos principales"}</p>
            </div>
            <button
              type="button"
              onClick={load}
              disabled={loading}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 text-lg text-slate-500 transition hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700 disabled:opacity-50"
              aria-label="Actualizar resumen"
              title="Actualizar"
            >
              <span aria-hidden="true">↻</span>
            </button>
          </div>

          {loading && !summary ? (
            <Spinner />
          ) : error ? (
            <div className="p-5"><Alert>{error}</Alert></div>
          ) : (
            <div className="space-y-1 p-3 sm:p-4">
              {summary?.items.map((item: DashboardItem) => <Row key={item.key} item={item} />)}
            </div>
          )}
        </section>

        <Banner />
      </div>
    </div>
  );
}

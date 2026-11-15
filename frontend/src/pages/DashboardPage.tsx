import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ACCESS_LEVEL_LABEL } from "../app/config";
import { useAuth } from "../app/AuthContext";
import { Alert, Badge, PageHeader } from "../components/ui";
import { documentTypesApi, draftsApi, integrationApi, officesApi, templatesApi, usersApi } from "../services/api";
import type { IntegrationStatus } from "../types";

interface Metric {
  label: string;
  value: number | null;
  to: string;
}

export function DashboardPage() {
  const { user, can } = useAuth();
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [integration, setIntegration] = useState<IntegrationStatus | null>(null);

  useEffect(() => {
    const count = async (label: string, to: string, call: () => Promise<{ count: number }>): Promise<Metric> => {
      try {
        return { label, to, value: (await call()).count };
      } catch {
        return { label, to, value: null };
      }
    };
    const jobs: Promise<Metric>[] = [
      count("Oficinas registradas", "/oficinas", () => officesApi.list({ page_size: 1 })),
      count("Tipos documentales", "/tipos-documentales", () => documentTypesApi.list({ page_size: 1 })),
      count("Plantillas visibles", "/plantillas", () => templatesApi.list({ page_size: 1 })),
      count("Mis borradores visibles", "/nuevo-documento", () => draftsApi.list({ page_size: 1 })),
    ];
    if (can(["users.view", "users.manage"])) jobs.push(count("Usuarios", "/usuarios", () => usersApi.list({ page_size: 1 })));
    Promise.all(jobs).then(setMetrics);
    integrationApi.status().then(setIntegration).catch(() => setIntegration(null));
  }, [can]);

  if (!user) return null;

  return (
    <div className="space-y-6">
      <PageHeader title={`Hola, ${user.first_name || user.username}`} subtitle="Panel administrativo inicial de la Fase 01." />

      <div className="grid gap-4 md:grid-cols-2">
        <section className="card p-4">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Su contexto</h2>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Oficina actual</dt><dd>{user.primary_office?.name ?? "—"}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Cargo</dt><dd>{user.primary_office?.position ?? "—"}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Nivel de visibilidad</dt><dd><Badge tone={user.access_level === "TOTAL" ? "blue" : "slate"}>{ACCESS_LEVEL_LABEL[user.access_level]}</Badge></dd></div>
          </dl>
          <p className="mt-3 text-xs text-slate-500">
            El nivel de acceso solo define qué documentos puede ver. Firmar, aprobar, emitir o anular depende de permisos y competencias aparte.
          </p>
        </section>

        <section className="card p-4">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Integración con SGDGuarmail</h2>
          {integration ? (
            <>
              <Badge tone={integration.implemented ? "green" : "amber"}>{integration.implemented ? "Disponible" : "No implementada"}</Badge>
              <p className="mt-2 text-sm text-slate-600">{integration.phase}</p>
            </>
          ) : (
            <p className="text-sm text-slate-500">Estado no disponible.</p>
          )}
        </section>
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-700">Resumen del sistema</h2>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          {metrics.map((m) => (
            <Link key={m.label} to={m.to} className="card p-4 hover:border-brand-300">
              <p className="text-2xl font-semibold text-brand-800">{m.value ?? "—"}</p>
              <p className="text-xs text-slate-500">{m.label}</p>
            </Link>
          ))}
        </div>
        <div className="mt-3">
          <Alert kind="info">Estas cifras se consultan en tiempo real a la base de datos del sistema. No hay indicadores simulados.</Alert>
        </div>
      </section>
    </div>
  );
}

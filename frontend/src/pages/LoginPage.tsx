import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { config } from "../app/config";
import { useAuth } from "../app/AuthContext";
import { Alert, Field } from "../components/ui";
import { errorMessage } from "../services/http";

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={from} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      const text = errorMessage(err);
      setError(text.includes("No active account") || text.startsWith("detail") ? "Usuario o contraseña incorrectos." : text);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-[#8b3d56] via-[#70233f] to-[#4e172d] p-4 sm:p-8">
      <div aria-hidden="true" className="pointer-events-none absolute -left-32 -top-40 h-96 w-96 rounded-full bg-rose-200/10 blur-3xl" />
      <div aria-hidden="true" className="pointer-events-none absolute -bottom-48 -right-24 h-[30rem] w-[30rem] rounded-full bg-black/10 blur-3xl" />
      <div className="relative grid w-full max-w-6xl items-center gap-5 md:grid-cols-[minmax(260px,0.95fr)_minmax(380px,1.05fr)] md:gap-10">
        <div className="flex min-h-[190px] items-center justify-center rounded-3xl border border-white/20 bg-white/10 p-2 shadow-xl backdrop-blur-sm sm:min-h-[240px] sm:p-3 md:min-h-[570px]">
          <img
            src="/images/SGD.png"
            alt="Personaje del Sistema de Gestión Documental de Huarmey"
            className="h-[190px] w-full rounded-2xl object-contain sm:h-[240px] md:h-[550px]"
          />
        </div>
        <div className="card w-full rounded-3xl border-white/60 p-6 shadow-2xl sm:p-9">
          <div className="mb-6 border-b border-slate-100 pb-5">
            <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.18em] text-[#8b3d56]">Acceso institucional</p>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">HUARMY SGD</h1>
            <p className="mt-1.5 text-sm text-slate-500">{config.institutionName}</p>
          </div>
          <p className="mb-6 text-sm leading-6 text-slate-600">Sistema de gestión documental. Ingrese con su usuario institucional.</p>
          <form onSubmit={submit} className="space-y-5">
            {error && <Alert>{error}</Alert>}
            <Field label="Usuario">
              <input className="input rounded-lg px-3.5 py-2.5 focus:border-[#8b3d56] focus:ring-[#8b3d56]" autoComplete="username" required autoFocus value={username} onChange={(e) => setUsername(e.target.value)} />
            </Field>
            <Field label="Contraseña">
              <input className="input rounded-lg px-3.5 py-2.5 focus:border-[#8b3d56] focus:ring-[#8b3d56]" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>
            <button type="submit" className="btn w-full rounded-lg bg-[#70233f] py-3 font-semibold text-white shadow-sm transition hover:bg-[#5b1b33] focus:ring-[#8b3d56]" disabled={busy}>
              {busy ? "Ingresando…" : "Ingresar"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

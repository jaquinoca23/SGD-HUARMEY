import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { config } from "../app/config";
import { useAuth } from "../app/AuthContext";
import { Alert, Field, Logo } from "../components/ui";
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
    <div className="flex min-h-screen items-center justify-center bg-brand-900 p-4">
      <div className="card w-full max-w-sm p-6">
        <div className="mb-5 flex items-center gap-3">
          <Logo name={config.institutionName} url={config.logoUrl} />
          <div className="leading-tight">
            <h1 className="text-lg font-bold text-brand-900">HUARMY SGD</h1>
            <p className="text-xs text-slate-500">{config.institutionName}</p>
          </div>
        </div>
        <p className="mb-4 text-sm text-slate-600">Sistema de gestión documental. Ingrese con su usuario institucional.</p>
        <form onSubmit={submit} className="space-y-4">
          {error && <Alert>{error}</Alert>}
          <Field label="Usuario">
            <input className="input" autoComplete="username" required autoFocus value={username} onChange={(e) => setUsername(e.target.value)} />
          </Field>
          <Field label="Contraseña">
            <input className="input" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
          <button type="submit" className="btn-primary w-full" disabled={busy}>
            {busy ? "Ingresando…" : "Ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}

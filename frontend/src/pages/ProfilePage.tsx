import { FormEvent, useState } from "react";

import { ACCESS_LEVEL_LABEL } from "../app/config";
import { useAuth } from "../app/AuthContext";
import { Alert, Badge, Field, PageHeader } from "../components/ui";
import { authApi } from "../services/api";
import { errorMessage } from "../services/http";

export function ProfilePage() {
  const { user, reloadUser } = useAuth();
  const [form, setForm] = useState({
    first_name: user?.first_name ?? "",
    last_name: user?.last_name ?? "",
    email: user?.email ?? "",
    phone: user?.phone ?? "",
  });
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [pwd, setPwd] = useState({ current: "", next: "" });
  const [pwdMsg, setPwdMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  if (!user) return null;

  const saveProfile = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await authApi.updateProfile(form);
      await reloadUser();
      setMsg({ kind: "success", text: "Perfil actualizado." });
    } catch (err) {
      setMsg({ kind: "error", text: errorMessage(err) });
    }
  };

  const changePassword = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await authApi.changePassword(pwd.current, pwd.next);
      setPwd({ current: "", next: "" });
      setPwdMsg({ kind: "success", text: "Contraseña actualizada." });
    } catch (err) {
      setPwdMsg({ kind: "error", text: errorMessage(err) });
    }
  };

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [key]: e.target.value });

  return (
    <div className="space-y-6">
      <PageHeader title="Mi perfil" subtitle={`Usuario: ${user.username}`} />

      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={saveProfile} className="card space-y-4 p-5">
          <h2 className="text-sm font-semibold">Datos personales</h2>
          {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
          <Field label="Nombres"><input className="input" required value={form.first_name} onChange={set("first_name")} /></Field>
          <Field label="Apellidos"><input className="input" required value={form.last_name} onChange={set("last_name")} /></Field>
          <Field label="Correo electrónico"><input className="input" type="email" required value={form.email} onChange={set("email")} /></Field>
          <Field label="Teléfono"><input className="input" value={form.phone} onChange={set("phone")} /></Field>
          <button type="submit" className="btn-primary">Guardar cambios</button>
        </form>

        <form onSubmit={changePassword} className="card space-y-4 p-5">
          <h2 className="text-sm font-semibold">Cambiar contraseña</h2>
          {pwdMsg && <Alert kind={pwdMsg.kind}>{pwdMsg.text}</Alert>}
          <Field label="Contraseña actual"><input className="input" type="password" autoComplete="current-password" required value={pwd.current} onChange={(e) => setPwd({ ...pwd, current: e.target.value })} /></Field>
          <Field label="Nueva contraseña" hint="Mínimo 10 caracteres; no puede ser común ni solo numérica."><input className="input" type="password" autoComplete="new-password" required value={pwd.next} onChange={(e) => setPwd({ ...pwd, next: e.target.value })} /></Field>
          <button type="submit" className="btn-primary">Actualizar contraseña</button>
        </form>
      </div>

      <section className="card p-5">
        <h2 className="mb-3 text-sm font-semibold">Oficinas y nivel de acceso</h2>
        {user.assignments.length === 0 ? (
          <p className="text-sm text-slate-500">No tiene oficinas asignadas vigentes.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {user.assignments.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{a.office.name}</span>
                {a.position && <span className="text-slate-500">· {a.position}</span>}
                <Badge tone={a.access_level === "TOTAL" ? "blue" : "slate"}>{ACCESS_LEVEL_LABEL[a.access_level]}</Badge>
                {a.is_primary && <Badge tone="green">Principal</Badge>}
                {a.is_acting && <Badge tone="amber">Encargatura</Badge>}
              </li>
            ))}
          </ul>
        )}
        <h3 className="mb-2 mt-5 text-sm font-semibold">Roles</h3>
        <div className="flex flex-wrap gap-2">
          {user.roles.length ? user.roles.map((r) => <Badge key={r}>{r}</Badge>) : <span className="text-sm text-slate-500">Sin roles.</span>}
        </div>
        <h3 className="mb-2 mt-5 text-sm font-semibold">Permisos efectivos</h3>
        <div className="flex flex-wrap gap-2">
          {user.permissions.length ? user.permissions.map((p) => <code key={p} className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">{p}</code>) : <span className="text-sm text-slate-500">Sin permisos.</span>}
        </div>
      </section>
    </div>
  );
}

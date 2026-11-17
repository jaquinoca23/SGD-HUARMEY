import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../app/AuthContext";
import { Spinner } from "../components/ui";

/** Exige sesión iniciada; si no, redirige a /login conservando la ruta pedida. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Spinner label="Verificando sesión…" />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}

/** Oculta pantallas para quien no tiene el permiso. El backend vuelve a validarlo en cada petición. */
export function RequirePermission({ permission, children }: { permission: string | string[]; children: ReactNode }) {
  const { can } = useAuth();
  if (!can(permission)) {
    return (
      <div className="card mx-auto mt-10 max-w-lg p-8 text-center">
        <p className="text-4xl">🔒</p>
        <h1 className="mt-3 text-lg font-semibold">Acceso restringido</h1>
        <p className="mt-2 text-sm text-slate-500">No tiene permiso para ver esta sección. Si lo necesita, solicítelo al administrador del sistema.</p>
      </div>
    );
  }
  return <>{children}</>;
}

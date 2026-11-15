import { isRouteErrorResponse, Link, useRouteError } from "react-router-dom";

/** Pantalla de error de rutas (errores de renderizado o rutas inválidas). */
export function ErrorPage() {
  const error = useRouteError();
  let title = "Ocurrió un error inesperado";
  let detail = "Recargue la página. Si el problema continúa, informe al administrador.";

  if (isRouteErrorResponse(error)) {
    title = error.status === 404 ? "Página no encontrada" : `Error ${error.status}`;
    detail = error.statusText || detail;
  } else if (import.meta.env.DEV && error instanceof Error) {
    detail = error.message; // solo en desarrollo: no se exponen detalles técnicos en producción
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <div className="card max-w-lg p-8 text-center">
        <p className="text-4xl">⚠️</p>
        <h1 className="mt-3 text-lg font-semibold">{title}</h1>
        <p className="mt-2 text-sm text-slate-500">{detail}</p>
        <div className="mt-5 flex justify-center gap-2">
          <button type="button" className="btn-secondary" onClick={() => window.location.reload()}>Recargar</button>
          <Link to="/" className="btn-primary">Ir al inicio</Link>
        </div>
      </div>
    </div>
  );
}

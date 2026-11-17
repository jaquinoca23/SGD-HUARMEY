import { Link } from "react-router-dom";

export function NotFoundPage({ standalone = false }: { standalone?: boolean }) {
  const content = (
    <div className="card mx-auto mt-10 max-w-lg p-8 text-center">
      <p className="text-5xl font-bold text-brand-700">404</p>
      <h1 className="mt-3 text-lg font-semibold">Página no encontrada</h1>
      <p className="mt-2 text-sm text-slate-500">La dirección que busca no existe o fue movida.</p>
      <Link to="/" className="btn-primary mt-5">Volver al inicio</Link>
    </div>
  );
  return standalone ? <div className="min-h-screen bg-slate-50 p-4">{content}</div> : content;
}

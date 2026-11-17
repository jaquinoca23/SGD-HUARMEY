import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { ACCESS_LEVEL_LABEL, config } from "../app/config";
import { useAuth } from "../app/AuthContext";
import { Badge, Logo } from "../components/ui";

interface MenuItem {
  to?: string;
  label: string;
  permission?: string | string[];
  /** Funcionalidad de una fase posterior: se muestra deshabilitada. */
  soon?: boolean;
}

interface MenuGroup {
  label: string;
  items: MenuItem[];
}

const MENU: MenuGroup[] = [
  {
    label: "Configuración",
    items: [
      { to: "/usuarios", label: "Usuarios", permission: ["users.view", "users.manage"] },
      { to: "/oficinas", label: "Oficinas" },
      { to: "/roles", label: "Roles y permisos", permission: ["users.view", "users.manage", "roles.manage"] },
      { to: "/tipos-documentales", label: "Tipos documentales" },
      { to: "/plantillas", label: "Plantillas" },
    ],
  },
  {
    label: "Documentos",
    items: [
      { to: "/", label: "Inicio" },
      { to: "/nuevo-documento", label: "Nuevo documento", permission: "documents.create" },
      { label: "Bandejas y derivaciones", soon: true },
    ],
  },
  { label: "Mesa de partes", items: [{ label: "Mesa de partes", soon: true }] },
  { label: "Consultas", items: [{ label: "Consulta de documentos", soon: true }] },
  { label: "Consultas generales", items: [{ label: "Consulta general", soon: true }] },
];

export function MainLayout() {
  const { user, logout, can } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openGroup, setOpenGroup] = useState<string | null>(null);
  const barRef = useRef<HTMLDivElement>(null);

  // Cierra los menús al navegar o al hacer clic fuera de la barra.
  useEffect(() => {
    setOpenGroup(null);
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (barRef.current && !barRef.current.contains(e.target as Node)) setOpenGroup(null);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  if (!user) return null;

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const office = user.primary_office;

  return (
    <div className="flex min-h-screen flex-col bg-slate-100">
      {/* Cabecera */}
      <header className="bg-white">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <Link to="/" className="flex items-center gap-3" aria-label="Ir al inicio">
            <Logo name={config.institutionName} url={config.logoUrl} />
            <div className="leading-tight">
              <p className="text-xl font-light text-brand-800 sm:text-2xl">Sistema de Gestión Documental</p>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">HUARMY SGD · {config.institutionName}</p>
            </div>
          </Link>

          <div className="order-3 w-full leading-tight sm:order-none sm:ml-auto sm:w-auto sm:flex-1">
            <p className="text-sm font-medium uppercase text-brand-800 sm:text-base">{office ? office.name : "Sin oficina asignada"}</p>
            <p className="text-xs uppercase text-slate-500">
              {user.full_name}
              {office?.position ? ` · ${office.position}` : ""}
            </p>
          </div>

          <div className="ml-auto flex items-center gap-3 sm:ml-0">
            <Badge tone={user.access_level === "TOTAL" ? "blue" : "slate"}>{ACCESS_LEVEL_LABEL[user.access_level]}</Badge>
            <Link to="/perfil" className="text-sm font-medium text-brand-700 hover:underline">Mi perfil</Link>
            <button type="button" onClick={handleLogout} className="flex items-center gap-1 text-sm font-bold text-slate-800 hover:text-red-600" aria-label="Cerrar sesión">
              Salir <span aria-hidden="true" className="text-xl">⎋</span>
            </button>
          </div>
        </div>

        {/* Barra de menú */}
        <div ref={barRef} className="border-y border-slate-200 bg-gradient-to-b from-white to-slate-100">
          <button type="button" className="px-4 py-2 text-sm font-semibold uppercase text-slate-600 md:hidden" onClick={() => setMobileOpen((v) => !v)} aria-expanded={mobileOpen}>
            ☰ Menú
          </button>
          <nav aria-label="Menú principal" className={`${mobileOpen ? "block" : "hidden"} md:flex`}>
            {MENU.map((group) => {
              const items = group.items.filter((item) => can(item.permission));
              if (items.length === 0) return null;
              const isOpen = openGroup === group.label;
              return (
                <div key={group.label} className="relative border-slate-200 md:border-r">
                  <button
                    type="button"
                    onClick={() => setOpenGroup(isOpen ? null : group.label)}
                    aria-haspopup="true"
                    aria-expanded={isOpen}
                    className={`w-full px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide md:w-auto ${isOpen ? "bg-white text-brand-700" : "text-slate-600 hover:bg-white"}`}
                  >
                    {group.label} <span aria-hidden="true" className="text-[9px]">▾</span>
                  </button>
                  {isOpen && (
                    <ul className="z-40 min-w-56 border border-slate-200 bg-white shadow-lg md:absolute md:left-0 md:top-full">
                      {items.map((item) => (
                        <li key={item.label}>
                          {item.to && !item.soon ? (
                            <NavLink
                              to={item.to}
                              end={item.to === "/"}
                              className={({ isActive }) => `block px-4 py-2 text-sm ${isActive ? "bg-brand-50 font-medium text-brand-800" : "text-slate-700 hover:bg-slate-50"}`}
                            >
                              {item.label}
                            </NavLink>
                          ) : (
                            <span className="flex items-center justify-between gap-3 px-4 py-2 text-sm text-slate-400" aria-disabled="true">
                              {item.label}
                              <span className="rounded bg-slate-100 px-1.5 text-[10px] uppercase">Próximamente</span>
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="flex-1 p-4 sm:p-6">
        <Outlet />
      </main>

      {/* Pie con datos de la unidad orgánica */}
      <footer className="border-t border-slate-300 bg-gradient-to-b from-slate-100 to-white px-4 py-3 text-xs text-slate-600">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-0.5">
            <p>Usuario: <span className="font-medium">{user.username}</span></p>
            <p>Versión {config.appVersion}</p>
            <p>Ruta de documentos: <span className="text-slate-500">no configurada (requiere SGDGuarmail, aún no implementado)</span></p>
          </div>
          <div className="space-y-0.5">
            <p>Unidad orgánica:</p>
            <p className="font-bold uppercase text-brand-800">{office ? office.name : "Sin oficina asignada"}</p>
            <p className="font-bold uppercase text-brand-800">{config.sedeName}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

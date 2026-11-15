import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { ACCESS_LEVEL_LABEL, config } from "../app/config";
import { useAuth } from "../app/AuthContext";
import { Badge, Logo } from "../components/ui";

interface MenuItem {
  to: string;
  label: string;
  permission?: string | string[];
  end?: boolean;
}

const MENU: { title?: string; items: MenuItem[] }[] = [
  {
    items: [
      { to: "/", label: "Inicio", end: true },
      { to: "/nuevo-documento", label: "Nuevo documento", permission: "documents.create" },
    ],
  },
  {
    title: "Administración",
    items: [
      { to: "/usuarios", label: "Usuarios", permission: ["users.view", "users.manage"] },
      { to: "/oficinas", label: "Oficinas" },
      { to: "/roles", label: "Roles y permisos", permission: ["users.view", "users.manage", "roles.manage"] },
      { to: "/tipos-documentales", label: "Tipos documentales" },
      { to: "/plantillas", label: "Plantillas" },
    ],
  },
  { title: "Cuenta", items: [{ to: "/perfil", label: "Mi perfil" }] },
];

export function MainLayout() {
  const { user, logout, can } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  if (!user) return null;

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const sidebar = (
    <nav aria-label="Navegación principal" className="flex h-full flex-col bg-brand-900 text-brand-50">
      <div className="flex items-center gap-3 border-b border-brand-800 px-4 py-4">
        <Logo name={config.institutionName} url={config.logoUrl} />
        <div className="leading-tight">
          <p className="text-sm font-bold tracking-wide">HUARMY SGD</p>
          <p className="text-[11px] text-brand-200">{config.institutionName}</p>
        </div>
      </div>
      <div className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {MENU.map((group, index) => {
          const items = group.items.filter((item) => can(item.permission));
          if (items.length === 0) return null;
          return (
            <div key={index}>
              {group.title && <p className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wider text-brand-300">{group.title}</p>}
              <ul className="space-y-1">
                {items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.end}
                      onClick={() => setOpen(false)}
                      className={({ isActive }) =>
                        `block rounded-md px-3 py-2 text-sm ${isActive ? "bg-brand-700 font-medium text-white" : "text-brand-100 hover:bg-brand-800"}`
                      }
                    >
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </nav>
  );

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 lg:block">
        <div className="fixed inset-y-0 w-64">{sidebar}</div>
      </aside>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/50" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-64">{sidebar}</div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3">
          <div className="flex items-center gap-3">
            <button type="button" className="btn-secondary lg:hidden" onClick={() => setOpen(true)} aria-label="Abrir menú">
              ☰
            </button>
            <div className="leading-tight">
              <p className="text-sm font-semibold text-slate-900">{user.full_name}</p>
              <p className="text-xs text-slate-500">
                {user.primary_office ? user.primary_office.name : "Sin oficina asignada"}
                {user.primary_office?.position ? ` · ${user.primary_office.position}` : ""}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge tone={user.access_level === "TOTAL" ? "blue" : "slate"}>{ACCESS_LEVEL_LABEL[user.access_level]}</Badge>
            <button type="button" className="btn-secondary" onClick={handleLogout}>
              Cerrar sesión
            </button>
          </div>
        </header>
        <main className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

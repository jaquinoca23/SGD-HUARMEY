import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { authApi } from "../services/api";
import { SESSION_EXPIRED_EVENT, tokenStore } from "../services/http";
import type { AuthUser } from "../types";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  reloadUser: () => Promise<void>;
  /** true si el usuario tiene el permiso (o alguno de la lista). Solo para mostrar/ocultar la interfaz:
   *  la autorización real siempre la aplica el backend. */
  can: (permission?: string | string[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(tokenStore.access));

  useEffect(() => {
    if (!tokenStore.access) return;
    authApi
      .me()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setUser(await authApi.login(username, password));
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const reloadUser = useCallback(async () => {
    setUser(await authApi.me());
  }, []);

  const can = useCallback(
    (permission?: string | string[]) => {
      if (!permission) return true;
      if (!user) return false;
      const wanted = Array.isArray(permission) ? permission : [permission];
      return wanted.some((code) => user.permissions.includes(code));
    },
    [user],
  );

  const value = useMemo(() => ({ user, loading, login, logout, reloadUser, can }), [user, loading, login, logout, reloadUser, can]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}

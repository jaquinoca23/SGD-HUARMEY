import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

import { config } from "../app/config";

/**
 * Los tokens se guardan en sessionStorage: se pierden al cerrar la pestaña. Es un compromiso
 * frente a cookies HttpOnly (ver docs/ARQUITECTURA.md, sección Seguridad). El access token dura 15 min.
 */
const ACCESS_KEY = "huarmy.access";
const REFRESH_KEY = "huarmy.refresh";

export const tokenStore = {
  get access() {
    return sessionStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return sessionStorage.getItem(REFRESH_KEY);
  },
  set(access: string, refresh?: string) {
    sessionStorage.setItem(ACCESS_KEY, access);
    if (refresh) sessionStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
  },
};

export const SESSION_EXPIRED_EVENT = "huarmy:session-expired";

export const http = axios.create({ baseURL: config.apiUrl, timeout: 30000 });

http.interceptors.request.use((request: InternalAxiosRequestConfig) => {
  const token = tokenStore.access;
  if (token) request.headers.Authorization = `Bearer ${token}`;
  return request;
});

let refreshing: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh = tokenStore.refresh;
  if (!refresh) throw new Error("Sin refresh token");
  // Se usa axios "plano" para no pasar por los interceptores.
  const { data } = await axios.post(`${config.apiUrl}/auth/refresh/`, { refresh });
  tokenStore.set(data.access, data.refresh);
  return data.access as string;
}

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
    const isAuthCall = original?.url?.includes("/auth/login") || original?.url?.includes("/auth/refresh");
    if (error.response?.status === 401 && original && !original._retried && !isAuthCall && tokenStore.refresh) {
      original._retried = true;
      try {
        refreshing = refreshing ?? refreshAccessToken().finally(() => (refreshing = null));
        const access = await refreshing;
        original.headers.Authorization = `Bearer ${access}`;
        return http(original);
      } catch {
        tokenStore.clear();
        window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
      }
    }
    return Promise.reject(error);
  },
);

/** Convierte los errores de DRF en un texto legible para mostrar al usuario. */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) return "No se pudo conectar con el servidor. Verifique que el backend esté en ejecución.";
    const { status, data } = error.response;
    if (status === 403) return (data?.detail as string) || "No tiene permiso para realizar esta acción.";
    if (status === 429) return "Demasiados intentos. Espere un momento e inténtelo de nuevo.";
    if (status >= 500) return "Error interno del servidor.";
    if (typeof data === "string") return data;
    if (data && typeof data === "object") {
      const parts: string[] = [];
      for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
        const text = Array.isArray(value) ? value.join(" ") : typeof value === "string" ? value : JSON.stringify(value);
        parts.push(key === "detail" || key === "non_field_errors" ? text : `${key}: ${text}`);
      }
      if (parts.length) return parts.join(" · ");
    }
    return `Error ${status}`;
  }
  return error instanceof Error ? error.message : "Error inesperado.";
}

import type {
  AppPermission, Assignment, AuthUser, DashboardSummary, DocumentDraft, DocumentType, IntegrationStatus, Office, OfficeNode,
  Paginated, Position, Role, Template, TemplateVersion, User,
} from "../types";
import { http, tokenStore } from "./http";

type Params = Record<string, string | number | boolean | undefined>;

/** CRUD genérico sobre un recurso paginado de la API. */
function resource<T>(path: string) {
  return {
    list: async (params?: Params) => (await http.get<Paginated<T>>(`/${path}/`, { params })).data,
    get: async (id: number) => (await http.get<T>(`/${path}/${id}/`)).data,
    create: async (body: unknown) => (await http.post<T>(`/${path}/`, body)).data,
    update: async (id: number, body: unknown) => (await http.patch<T>(`/${path}/${id}/`, body)).data,
    remove: async (id: number) => {
      await http.delete(`/${path}/${id}/`);
    },
  };
}

export const authApi = {
  async login(username: string, password: string): Promise<AuthUser> {
    const { data } = await http.post("/auth/login/", { username, password });
    tokenStore.set(data.access, data.refresh);
    return data.user as AuthUser;
  },
  async logout() {
    const refresh = tokenStore.refresh;
    try {
      if (refresh) await http.post("/auth/logout/", { refresh });
    } finally {
      tokenStore.clear();
    }
  },
  me: async () => (await http.get<AuthUser>("/auth/me/")).data,
  updateProfile: async (body: Partial<Pick<AuthUser, "first_name" | "last_name" | "email" | "phone">>) =>
    (await http.patch<AuthUser>("/auth/me/", body)).data,
  changePassword: async (current_password: string, new_password: string) => {
    await http.post("/auth/change-password/", { current_password, new_password });
  },
};

export const usersApi = resource<User>("users");
export const officesApi = {
  ...resource<Office>("offices"),
  tree: async () => (await http.get<OfficeNode[]>("/offices/tree/")).data,
};
export const positionsApi = resource<Position>("positions");
export const assignmentsApi = resource<Assignment>("assignments");
export const rolesApi = resource<Role>("roles");
export const permissionsApi = {
  list: async () => (await http.get<AppPermission[]>("/permissions/")).data,
};
export const documentTypesApi = resource<DocumentType>("document-types");
export const draftsApi = resource<DocumentDraft>("drafts");

export const templatesApi = {
  ...resource<Template>("templates"),
  versions: async (id: number) => (await http.get<TemplateVersion[]>(`/templates/${id}/versions/`)).data,
  uploadVersion: async (id: number, form: FormData) =>
    (await http.post<TemplateVersion>(`/templates/${id}/versions/`, form)).data,
  setCurrent: async (id: number, version_id: number) =>
    (await http.post<Template>(`/templates/${id}/set-current/`, { version_id })).data,
  async download(version: TemplateVersion) {
    const response = await http.get(`/template-versions/${version.id}/download/`, { responseType: "blob" });
    const url = URL.createObjectURL(response.data as Blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = version.file_name;
    link.click();
    URL.revokeObjectURL(url);
  },
};

export const dashboardApi = {
  summary: async () => (await http.get<DashboardSummary>("/dashboard/summary/")).data,
};

export const integrationApi = {
  status: async () => (await http.get<IntegrationStatus>("/integration/status/")).data,
};

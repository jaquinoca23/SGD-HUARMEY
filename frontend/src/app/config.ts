/** Configuración institucional editable mediante variables de entorno. */
export const config = {
  apiUrl: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
  institutionName: import.meta.env.VITE_INSTITUTION_NAME ?? "Municipalidad Provincial de Huarmey",
  logoUrl: import.meta.env.VITE_INSTITUTION_LOGO_URL ?? "",
  sedeName: import.meta.env.VITE_INSTITUTION_SEDE ?? "Sede central",
  appVersion: "0.1 (Fase 01)",
};

export const ACCESS_LEVEL_LABEL = {
  PERSONAL: "Acceso personal",
  TOTAL: "Acceso total de la oficina",
} as const;

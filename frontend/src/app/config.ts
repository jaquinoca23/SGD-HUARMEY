/** Configuración institucional editable mediante variables de entorno. */
export const config = {
  apiUrl: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
  institutionName: import.meta.env.VITE_INSTITUTION_NAME ?? "Municipalidad Provincial de Huarmey",
  logoUrl: import.meta.env.VITE_INSTITUTION_LOGO_URL ?? "",
};

export const ACCESS_LEVEL_LABEL = {
  PERSONAL: "Acceso personal",
  TOTAL: "Acceso total de la oficina",
} as const;

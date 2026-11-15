/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_INSTITUTION_NAME?: string;
  readonly VITE_INSTITUTION_LOGO_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

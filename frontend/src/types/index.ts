export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type AccessLevel = "PERSONAL" | "TOTAL";

export interface OfficeRef {
  id: number;
  code: string;
  name: string;
}

export interface AuthAssignment {
  id: number;
  office: OfficeRef;
  position: string | null;
  access_level: AccessLevel;
  is_primary: boolean;
  is_acting: boolean;
}

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  is_superuser: boolean;
  permissions: string[];
  roles: string[];
  access_level: AccessLevel;
  primary_office: (OfficeRef & { position: string | null }) | null;
  assignments: AuthAssignment[];
}

export interface RoleRef {
  id: number;
  code: string;
  name: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  document_number: string | null;
  phone: string;
  is_active: boolean;
  last_login: string | null;
  roles: RoleRef[];
  role_ids: number[];
  extra_permission_ids: number[];
  primary_office: { id: number; name: string } | null;
  access_level: AccessLevel;
}

export type OfficeKind = "GOVERNING" | "GENERAL" | "MANAGEMENT" | "UNIT" | "OTHER";

export interface Office {
  id: number;
  code: string;
  name: string;
  kind: OfficeKind;
  kind_display: string;
  parent: number | null;
  parent_name: string | null;
  is_active: boolean;
  sort_order: number;
  children_count: number;
}

export interface OfficeNode {
  id: number;
  code: string;
  name: string;
  kind: OfficeKind;
  is_active: boolean;
  parent: number | null;
  children: OfficeNode[];
}

export interface Position {
  id: number;
  code: string;
  name: string;
  is_head: boolean;
  is_active: boolean;
}

export interface Assignment {
  id: number;
  user: number;
  user_name: string;
  office: number;
  office_name: string;
  position: number | null;
  position_name: string | null;
  access_level: AccessLevel;
  is_primary: boolean;
  is_acting: boolean;
  is_active: boolean;
}

export interface AppPermission {
  id: number;
  code: string;
  name: string;
  description: string;
  category: "ADMINISTRATION" | "OPERATIONAL" | "SIGNATURE";
  category_display: string;
}

export interface Role {
  id: number;
  code: string;
  name: string;
  description: string;
  permission_ids: number[];
  permission_codes: string[];
  is_system: boolean;
  is_active: boolean;
  users_count: number;
}

export type IssuanceScope = "OFFICE" | "INTERNAL" | "EXTERNAL" | "NORMATIVE";

export interface DocumentType {
  id: number;
  code: string;
  name: string;
  description: string;
  requires_signature: boolean;
  issuance_scope: IssuanceScope;
  issuance_scope_display: string;
  allows_multiple_recipients: boolean;
  default_template: number | null;
  default_template_name: string | null;
  is_active: boolean;
  sort_order: number;
}

export interface TemplateVersion {
  id: number;
  template: number;
  version_number: number;
  version_label: string;
  file_name: string;
  file_size: number;
  checksum_sha256: string;
  is_official: boolean;
  notes: string;
  created_by_name: string | null;
  created_at: string;
  is_current: boolean;
}

export interface Template {
  id: number;
  name: string;
  description: string;
  document_type: number;
  document_type_name: string;
  office: number | null;
  office_name: string | null;
  is_private: boolean;
  is_active: boolean;
  current_version: number | null;
  current_version_detail: TemplateVersion | null;
  versions_count: number;
}

export interface DocumentDraft {
  id: number;
  public_id: string;
  title: string;
  document_type: number;
  document_type_name: string;
  office: number;
  office_name: string;
  author_name: string;
  assigned_to_name: string | null;
  status: string;
  confidentiality: "NORMAL" | "CONFIDENTIAL";
  template_name: string | null;
  template_version_number: number | null;
  template_is_official: boolean | null;
  template_resolved: boolean;
  created_at: string;
}

export interface IntegrationStatus {
  agent: string;
  implemented: boolean;
  phase: string;
  planned_flow: string[];
}

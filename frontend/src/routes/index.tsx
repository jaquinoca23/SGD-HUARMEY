import { createBrowserRouter } from "react-router-dom";

import { MainLayout } from "../layouts/MainLayout";
import { DocumentTypesPage } from "../modules/document-types/DocumentTypesPage";
import { OfficesPage } from "../modules/offices/OfficesPage";
import { RolesPage } from "../modules/roles/RolesPage";
import { TemplatesPage } from "../modules/templates/TemplatesPage";
import { UsersPage } from "../modules/users/UsersPage";
import { DashboardPage } from "../pages/DashboardPage";
import { ErrorPage } from "../pages/ErrorPage";
import { LoginPage } from "../pages/LoginPage";
import { NewDocumentPage } from "../pages/NewDocumentPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { ProfilePage } from "../pages/ProfilePage";
import { RequireAuth, RequirePermission } from "./guards";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage />, errorElement: <ErrorPage /> },
  {
    path: "/",
    element: (
      <RequireAuth>
        <MainLayout />
      </RequireAuth>
    ),
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <DashboardPage /> },
      {
        path: "nuevo-documento",
        element: (
          <RequirePermission permission="documents.create">
            <NewDocumentPage />
          </RequirePermission>
        ),
      },
      {
        path: "usuarios",
        element: (
          <RequirePermission permission={["users.view", "users.manage"]}>
            <UsersPage />
          </RequirePermission>
        ),
      },
      { path: "oficinas", element: <OfficesPage /> },
      {
        path: "roles",
        element: (
          <RequirePermission permission={["users.view", "users.manage", "roles.manage"]}>
            <RolesPage />
          </RequirePermission>
        ),
      },
      { path: "tipos-documentales", element: <DocumentTypesPage /> },
      { path: "plantillas", element: <TemplatesPage /> },
      { path: "perfil", element: <ProfilePage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage standalone /> },
]);

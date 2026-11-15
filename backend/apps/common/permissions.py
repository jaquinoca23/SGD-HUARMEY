"""Permiso por acción para ViewSets (falla cerrado).

Cada vista declara `permission_map`, por ejemplo::

    permission_map = {
        "list": ANY_AUTHENTICATED,
        "create": "offices.manage",
        "versions:post": "templates.manage",   # acción:método
        "*": None,                              # cualquier otra acción -> denegada
    }

Un valor puede ser un código, una lista de códigos (basta uno) o ANY_AUTHENTICATED.
"""
from rest_framework.permissions import BasePermission

from apps.permissions.services import user_has_permission

ANY_AUTHENTICATED = "__authenticated__"


class ActionPermission(BasePermission):
    message = "No tiene permiso para realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.is_active):
            return False
        pmap = getattr(view, "permission_map", None)
        if pmap is None:
            return False
        action = getattr(view, "action", None) or request.method.lower()
        method = request.method.lower()
        required = pmap.get(f"{action}:{method}", pmap.get(action, pmap.get("*")))
        if required is None:
            return False
        if required == ANY_AUTHENTICATED:
            return True
        codes = [required] if isinstance(required, str) else list(required)
        return any(user_has_permission(user, code) for code in codes)

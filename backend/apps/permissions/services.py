from .models import AppPermission


def get_user_permission_codes(user) -> set:
    """Códigos de permiso efectivos: roles activos + permisos directos. Superusuario: todos.

    El resultado se guarda en el objeto `user` durante su vida (normalmente una petición).
    Use clear_permission_cache(user) si cambia sus roles dentro del mismo objeto.
    """
    if user is None or not getattr(user, "is_authenticated", False) or not user.is_active:
        return set()
    cached = getattr(user, "_permission_codes", None)
    if cached is not None:
        return cached
    if user.is_superuser:
        codes = set(AppPermission.objects.values_list("code", flat=True))
    else:
        from_roles = AppPermission.objects.filter(roles__is_active=True, roles__users=user)
        direct = AppPermission.objects.filter(direct_users=user)
        codes = set(from_roles.values_list("code", flat=True)) | set(direct.values_list("code", flat=True))
    user._permission_codes = codes
    return codes


def clear_permission_cache(user):
    if hasattr(user, "_permission_codes"):
        del user._permission_codes


def user_has_permission(user, code: str) -> bool:
    return code in get_user_permission_codes(user)

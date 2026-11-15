from .models import AuditLog

_SENSITIVE_FIELDS = {"password", "last_login"}


def snapshot(instance) -> dict:
    """Valores serializables de los campos concretos de un modelo (sin datos sensibles)."""
    data = {}
    for field in instance._meta.concrete_fields:
        if field.name in _SENSITIVE_FIELDS:
            continue
        value = getattr(instance, field.attname)
        data[field.name] = value if isinstance(value, (str, int, float, bool, type(None))) else str(value)
    return data


def client_ip(request):
    meta = getattr(request, "META", {}) or {}
    return meta.get("REMOTE_ADDR") or None


def log_action(request, action, instance=None, *, entity_type=None, entity_id=None,
               changes=None, office=None, actor=None):
    """Registra una acción. `actor` se indica solo cuando aún no hay usuario autenticado (login)."""
    user = actor if actor is not None else getattr(request, "user", None)
    if user is not None and not getattr(user, "is_authenticated", False):
        user = None
    if instance is not None:
        entity_type = entity_type or instance._meta.label
        entity_id = entity_id if entity_id is not None else instance.pk
    return AuditLog.objects.create(
        actor=user,
        actor_username=getattr(user, "username", "") if user else "",
        action=action,
        entity_type=entity_type or "",
        entity_id="" if entity_id is None else str(entity_id),
        entity_repr=str(instance)[:255] if instance is not None else "",
        office=office,
        changes=changes or {},
        ip_address=client_ip(request),
    )

from django.db.models import Q
from django.utils import timezone

from .models import Assignment, Office


def active_assignments(user):
    """Asignaciones vigentes hoy (activas y dentro de su rango de fechas)."""
    if not user or not user.is_authenticated:
        return Assignment.objects.none()
    today = timezone.localdate()
    return (
        Assignment.objects.filter(user=user, is_active=True, office__is_active=True)
        .filter(Q(starts_on__isnull=True) | Q(starts_on__lte=today))
        .filter(Q(ends_on__isnull=True) | Q(ends_on__gte=today))
        .select_related("office", "position")
    )


def primary_assignment(user):
    qs = active_assignments(user)
    return qs.filter(is_primary=True).first() or qs.first()


def access_level_for(user) -> str:
    assignment = primary_assignment(user)
    return assignment.access_level if assignment else Assignment.AccessLevel.PERSONAL


def user_office_ids(user) -> set:
    return set(active_assignments(user).values_list("office_id", flat=True))


def total_access_office_ids(user) -> set:
    """Oficinas donde el usuario tiene acceso total (visibilidad de toda la oficina)."""
    return set(
        active_assignments(user)
        .filter(access_level=Assignment.AccessLevel.TOTAL)
        .values_list("office_id", flat=True)
    )


def would_create_cycle(office_pk, parent) -> bool:
    """True si asignar `parent` como superior de la oficina `office_pk` crea un ciclo."""
    node = parent
    seen = set()
    while node is not None:
        if office_pk is not None and node.pk == office_pk:
            return True
        if node.pk in seen:
            return True
        seen.add(node.pk)
        node = node.parent
    return False


def office_tree(queryset=None):
    """Árbol anidado de oficinas (lista de dicts con `children`)."""
    offices = list(queryset if queryset is not None else Office.objects.all())
    nodes = {o.pk: {"id": o.pk, "code": o.code, "name": o.name, "kind": o.kind,
                    "is_active": o.is_active, "parent": o.parent_id, "children": []} for o in offices}
    roots = []
    for node in nodes.values():
        parent = nodes.get(node["parent"])
        (parent["children"] if parent else roots).append(node)
    return roots

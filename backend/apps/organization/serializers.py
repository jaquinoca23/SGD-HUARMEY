from django.db import transaction
from rest_framework import serializers

from .models import Assignment, Office, Position
from .services import would_create_cycle


class OfficeSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True, default=None)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    children_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Office
        fields = [
            "id", "code", "name", "kind", "kind_display", "parent", "parent_name",
            "is_active", "sort_order", "children_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        return value.strip().upper()

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        pk = self.instance.pk if self.instance else None
        name = attrs.get("name", getattr(self.instance, "name", None))
        if name:
            same_name = Office.objects.filter(parent=parent, name__iexact=name)
            if pk is not None:
                same_name = same_name.exclude(pk=pk)
            if same_name.exists():
                raise serializers.ValidationError({"name": "Ya existe una oficina con ese nombre en la misma dependencia."})
        if parent is not None:
            if pk is not None and would_create_cycle(pk, parent):
                raise serializers.ValidationError({"parent": "La dependencia crearía un ciclo en la jerarquía."})
            if not parent.is_active and (self.instance is None or parent.pk != getattr(self.instance, "parent_id", None)):
                raise serializers.ValidationError({"parent": "La oficina superior está inactiva."})
        if self.instance and attrs.get("is_active") is False and self.instance.children.filter(is_active=True).exists():
            raise serializers.ValidationError({"is_active": "Desactive primero las dependencias hijas activas."})
        return attrs


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["id", "code", "name", "is_head", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        return value.strip().upper()


class AssignmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    office_name = serializers.CharField(source="office.name", read_only=True)
    position_name = serializers.CharField(source="position.name", read_only=True, default=None)

    class Meta:
        model = Assignment
        fields = [
            "id", "user", "user_name", "office", "office_name", "position", "position_name",
            "access_level", "is_primary", "is_acting", "is_active", "starts_on", "ends_on",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        starts = attrs.get("starts_on", getattr(self.instance, "starts_on", None))
        ends = attrs.get("ends_on", getattr(self.instance, "ends_on", None))
        if starts and ends and ends < starts:
            raise serializers.ValidationError({"ends_on": "La fecha final no puede ser anterior a la inicial."})
        office = attrs.get("office", getattr(self.instance, "office", None))
        is_active = attrs.get("is_active", getattr(self.instance, "is_active", True))
        if office is not None and is_active and not office.is_active:
            raise serializers.ValidationError({"office": "La oficina está inactiva."})
        user = attrs.get("user", getattr(self.instance, "user", None))
        if user is not None and office is not None and is_active:
            clash = Assignment.objects.filter(user=user, office=office, is_active=True)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError("El usuario ya tiene una asignación vigente en esa oficina.")
        return attrs

    @staticmethod
    def _normalize_primary(instance):
        """Garantiza una sola oficina principal vigente por usuario."""
        siblings = Assignment.objects.filter(user=instance.user, is_active=True).exclude(pk=instance.pk)
        if instance.is_active and instance.is_primary:
            siblings.update(is_primary=False)
        elif not siblings.filter(is_primary=True).exists() and instance.is_active:
            Assignment.objects.filter(pk=instance.pk).update(is_primary=True)
            instance.is_primary = True

    @transaction.atomic
    def create(self, validated_data):
        if validated_data.get("is_primary"):
            Assignment.objects.filter(user=validated_data["user"], is_active=True).update(is_primary=False)
        instance = super().create(validated_data)
        self._normalize_primary(instance)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        if validated_data.get("is_primary") and validated_data.get("is_active", instance.is_active):
            Assignment.objects.filter(user=instance.user, is_active=True).exclude(pk=instance.pk).update(is_primary=False)
        instance = super().update(instance, validated_data)
        self._normalize_primary(instance)
        return instance

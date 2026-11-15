from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.organization.services import access_level_for, active_assignments, primary_assignment
from apps.permissions.models import AppPermission, Role
from apps.permissions.services import get_user_permission_codes

User = get_user_model()


def _assignment_dict(a):
    return {
        "id": a.id,
        "office": {"id": a.office_id, "code": a.office.code, "name": a.office.name},
        "position": a.position.name if a.position else None,
        "access_level": a.access_level,
        "is_primary": a.is_primary,
        "is_acting": a.is_acting,
    }


class MeSerializer(serializers.ModelSerializer):
    """Usuario autenticado con permisos efectivos, oficina actual y nivel de acceso."""

    full_name = serializers.CharField(read_only=True)
    permissions = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    access_level = serializers.SerializerMethodField()
    primary_office = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "full_name", "phone",
            "is_superuser", "permissions", "roles", "access_level", "primary_office", "assignments",
        ]
        read_only_fields = ["id", "username", "is_superuser"]

    def get_permissions(self, obj):
        return sorted(get_user_permission_codes(obj))

    def get_roles(self, obj):
        return sorted(obj.roles.filter(is_active=True).values_list("code", flat=True))

    def get_access_level(self, obj):
        return access_level_for(obj)

    def get_primary_office(self, obj):
        a = primary_assignment(obj)
        return {"id": a.office_id, "code": a.office.code, "name": a.office.name,
                "position": a.position.name if a.position else None} if a else None

    def get_assignments(self, obj):
        return [_assignment_dict(a) for a in active_assignments(obj)]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Campos que el propio usuario puede editar de su perfil."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = MeSerializer(self.user, context=self.context).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserReadSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    roles = serializers.SerializerMethodField()
    role_ids = serializers.SerializerMethodField()
    extra_permission_ids = serializers.SerializerMethodField()
    primary_office = serializers.SerializerMethodField()
    access_level = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "full_name", "document_number",
            "phone", "is_active", "last_login", "date_joined", "roles", "role_ids",
            "extra_permission_ids", "primary_office", "access_level",
        ]
        read_only_fields = fields

    def get_roles(self, obj):
        return [{"id": r.id, "code": r.code, "name": r.name} for r in obj.roles.all()]

    def get_role_ids(self, obj):
        return [r.id for r in obj.roles.all()]

    def get_extra_permission_ids(self, obj):
        return [p.id for p in obj.extra_permissions.all()]

    def get_primary_office(self, obj):
        a = primary_assignment(obj)
        return {"id": a.office_id, "name": a.office.name} if a else None

    def get_access_level(self, obj):
        return access_level_for(obj)


class UserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={"input_type": "password"})
    role_ids = serializers.PrimaryKeyRelatedField(
        source="roles", many=True, queryset=Role.objects.filter(is_active=True), required=False, write_only=True
    )
    extra_permission_ids = serializers.PrimaryKeyRelatedField(
        source="extra_permissions", many=True, queryset=AppPermission.objects.all(), required=False, write_only=True
    )

    class Meta:
        model = User
        fields = [
            "username", "email", "first_name", "last_name", "document_number", "phone",
            "is_active", "password", "role_ids", "extra_permission_ids",
        ]
        extra_kwargs = {"document_number": {"required": False, "allow_null": True}}

    def to_representation(self, instance):
        return UserReadSerializer(instance, context=self.context).data

    def validate_document_number(self, value):
        return value or None

    def validate(self, attrs):
        actor = self.context["request"].user
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "La contraseña es obligatoria al crear un usuario."})
        if self.instance is not None and self.instance.is_superuser and not actor.is_superuser:
            raise PermissionDenied("Solo un superusuario puede modificar a otro superusuario.")
        if attrs.get("password"):
            validate_password(attrs["password"], self.instance)
        self._check_no_escalation(actor, attrs.get("roles", []), attrs.get("extra_permissions", []))
        return attrs

    @staticmethod
    def _check_no_escalation(actor, roles, extra_permissions):
        if actor.is_superuser:
            return
        needed = set(AppPermission.objects.filter(roles__in=roles).values_list("code", flat=True))
        needed |= {p.code for p in extra_permissions}
        missing = needed - get_user_permission_codes(actor)
        if missing:
            raise serializers.ValidationError(
                {"role_ids": f"No puede conceder permisos que usted no posee: {', '.join(sorted(missing))}."}
            )

    @transaction.atomic
    def create(self, validated_data):
        actor = self.context["request"].user
        roles = validated_data.pop("roles", [])
        extra = validated_data.pop("extra_permissions", [])
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        user.roles.set(roles, through_defaults={"assigned_by": actor})
        user.extra_permissions.set(extra, through_defaults={"assigned_by": actor})
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        actor = self.context["request"].user
        roles = validated_data.pop("roles", None)
        extra = validated_data.pop("extra_permissions", None)
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        if roles is not None:
            instance.roles.set(roles, through_defaults={"assigned_by": actor})
        if extra is not None:
            instance.extra_permissions.set(extra, through_defaults={"assigned_by": actor})
        return instance

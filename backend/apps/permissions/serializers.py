from rest_framework import serializers

from .models import AppPermission, Role, SigningAuthority


class AppPermissionSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = AppPermission
        fields = ["id", "code", "name", "description", "category", "category_display"]
        read_only_fields = fields


class RoleSerializer(serializers.ModelSerializer):
    permission_ids = serializers.PrimaryKeyRelatedField(
        source="permissions", many=True, queryset=AppPermission.objects.all(), required=False
    )
    permission_codes = serializers.SerializerMethodField()
    users_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Role
        fields = [
            "id", "code", "name", "description", "permission_ids", "permission_codes",
            "is_system", "is_active", "users_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]

    def get_permission_codes(self, obj):
        return sorted(p.code for p in obj.permissions.all())

    def validate_code(self, value):
        value = value.strip().upper()
        if self.instance and self.instance.is_system and value != self.instance.code:
            raise serializers.ValidationError("No se puede cambiar el código de un rol del sistema.")
        return value

    def validate_permission_ids(self, permissions):
        """Quien edita roles no puede conceder permisos que no posee (evita escalada)."""
        from .services import get_user_permission_codes

        actor = self.context["request"].user
        if actor.is_superuser:
            return permissions
        missing = {p.code for p in permissions} - get_user_permission_codes(actor)
        if missing:
            raise serializers.ValidationError(
                f"No puede conceder permisos que usted no posee: {', '.join(sorted(missing))}."
            )
        return permissions


class SigningAuthoritySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    office_name = serializers.CharField(source="office.name", read_only=True)
    document_type_name = serializers.CharField(source="document_type.name", read_only=True, default=None)

    class Meta:
        model = SigningAuthority
        fields = [
            "id", "user", "user_name", "office", "office_name", "document_type", "document_type_name",
            "basis", "valid_from", "valid_until", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("valid_from", getattr(self.instance, "valid_from", None))
        end = attrs.get("valid_until", getattr(self.instance, "valid_until", None))
        if start and end and end < start:
            raise serializers.ValidationError({"valid_until": "La vigencia final no puede ser anterior a la inicial."})
        return attrs

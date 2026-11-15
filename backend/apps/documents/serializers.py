from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.document_types.models import DocumentType
from apps.organization.models import Office
from apps.organization.services import primary_assignment, user_office_ids

from .models import DocumentDraft
from .services import resolve_template_version

User = get_user_model()


class DocumentDraftSerializer(serializers.ModelSerializer):
    document_type_name = serializers.CharField(source="document_type.name", read_only=True)
    office_name = serializers.CharField(source="office.name", read_only=True)
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True, default=None)
    template_name = serializers.CharField(source="template_version.template.name", read_only=True, default=None)
    template_version_number = serializers.IntegerField(source="template_version.version_number", read_only=True, default=None)
    template_is_official = serializers.BooleanField(source="template_version.is_official", read_only=True, default=None)
    template_resolved = serializers.SerializerMethodField()

    document_type = serializers.PrimaryKeyRelatedField(queryset=DocumentType.objects.filter(is_active=True))
    office = serializers.PrimaryKeyRelatedField(queryset=Office.objects.filter(is_active=True), required=False)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True), required=False, allow_null=True
    )

    class Meta:
        model = DocumentDraft
        fields = [
            "id", "public_id", "title", "document_type", "document_type_name", "office", "office_name",
            "author", "author_name", "assigned_to", "assigned_to_name", "status", "confidentiality",
            "template_version", "template_name", "template_version_number", "template_is_official",
            "template_resolved", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "public_id", "author", "status", "template_version", "created_at", "updated_at"]

    def get_template_resolved(self, obj):
        return obj.template_version_id is not None

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El título es obligatorio.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if self.instance is not None:
            # Tras crear, solo se editan título y confidencialidad.
            for locked in ("document_type", "office"):
                if locked in attrs and attrs[locked] != getattr(self.instance, locked):
                    raise serializers.ValidationError({locked: "No se puede cambiar después de crear el borrador."})
            return attrs

        office = attrs.get("office")
        if office is None:
            assignment = primary_assignment(user)
            if assignment is None:
                raise serializers.ValidationError("Su usuario no tiene una oficina asignada vigente.")
            office = assignment.office
            attrs["office"] = office
        elif office.pk not in user_office_ids(user):
            raise serializers.ValidationError({"office": "No pertenece a esa oficina."})

        assignee = attrs.get("assigned_to")
        if assignee is not None and assignee.pk != user.pk and office.pk not in user_office_ids(assignee):
            raise serializers.ValidationError(
                {"assigned_to": "Solo puede derivar a compañeros de la misma oficina."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        validated_data["template_version"] = resolve_template_version(
            validated_data["document_type"], validated_data["office"]
        )
        return super().create(validated_data)

from rest_framework import serializers

from .models import Template, TemplateVersion
from .validators import validate_docx_upload


class TemplateVersionSerializer(serializers.ModelSerializer):
    is_current = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True, default=None)
    file_name = serializers.CharField(source="download_name", read_only=True)

    class Meta:
        model = TemplateVersion
        fields = [
            "id", "template", "version_number", "version_label", "file_name", "file_size",
            "checksum_sha256", "is_official", "notes", "created_by_name", "created_at", "is_current",
        ]
        read_only_fields = fields

    def get_is_current(self, obj):
        return obj.template.current_version_id == obj.id


class TemplateVersionUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)
    version_label = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    is_official = serializers.BooleanField(required=False, default=False)
    set_current = serializers.BooleanField(required=False, default=True)

    def validate_file(self, uploaded):
        from django.core.exceptions import ValidationError as DjangoValidationError

        try:
            return validate_docx_upload(uploaded)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class SetCurrentSerializer(serializers.Serializer):
    version_id = serializers.IntegerField()


class TemplateSerializer(serializers.ModelSerializer):
    document_type_name = serializers.CharField(source="document_type.name", read_only=True)
    office_name = serializers.CharField(source="office.name", read_only=True, default=None)
    current_version_detail = TemplateVersionSerializer(source="current_version", read_only=True)
    versions_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Template
        fields = [
            "id", "name", "description", "document_type", "document_type_name", "office", "office_name",
            "is_private", "is_active", "current_version", "current_version_detail", "versions_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "current_version", "created_at", "updated_at"]

    def validate(self, attrs):
        get = lambda k: attrs.get(k, getattr(self.instance, k, None))  # noqa: E731
        office, is_private, is_active, doc_type = get("office"), get("is_private"), get("is_active"), get("document_type")
        if is_private and office is None:
            raise serializers.ValidationError({"office": "Una plantilla privada debe indicar la oficina."})
        if office is not None and not office.is_active:
            raise serializers.ValidationError({"office": "La oficina está inactiva."})
        if is_active is None:
            is_active = True
        if is_active:
            clash = Template.objects.filter(document_type=doc_type, office=office, is_active=True)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    "Ya existe una plantilla activa para ese tipo documental y oficina. "
                    "Cree una nueva versión o desactive la otra."
                )
        return attrs

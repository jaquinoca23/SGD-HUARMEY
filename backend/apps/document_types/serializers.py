from rest_framework import serializers

from .models import DocumentType


class DocumentTypeSerializer(serializers.ModelSerializer):
    issuance_scope_display = serializers.CharField(source="get_issuance_scope_display", read_only=True)
    default_template_name = serializers.CharField(source="default_template.name", read_only=True, default=None)

    class Meta:
        model = DocumentType
        fields = [
            "id", "code", "name", "description", "requires_signature", "issuance_scope",
            "issuance_scope_display", "allows_multiple_recipients", "default_template",
            "default_template_name", "is_active", "sort_order", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        return value.strip().upper().replace(" ", "_")

    def validate_default_template(self, template):
        if template is None:
            return template
        instance_pk = self.instance.pk if self.instance else None
        if instance_pk is None or template.document_type_id != instance_pk:
            raise serializers.ValidationError("La plantilla predeterminada debe pertenecer a este tipo documental.")
        if not template.is_active:
            raise serializers.ValidationError("La plantilla seleccionada está inactiva.")
        return template

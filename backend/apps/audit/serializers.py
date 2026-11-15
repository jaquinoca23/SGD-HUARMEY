from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    office_name = serializers.CharField(source="office.name", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id", "created_at", "actor", "actor_username", "action", "entity_type",
            "entity_id", "entity_repr", "office", "office_name", "changes", "ip_address",
        ]
        read_only_fields = fields

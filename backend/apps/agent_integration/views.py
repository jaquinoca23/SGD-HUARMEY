from rest_framework.response import Response
from rest_framework.views import APIView

from .interfaces import PLANNED_FLOW


class IntegrationStatusView(APIView):
    """Informa con honestidad que la integración con SGDGuarmail aún no existe."""

    def get(self, request):
        return Response({
            "agent": "SGDGuarmail",
            "implemented": False,
            "phase": "Fase 01: solo estructura, contratos y documentación",
            "planned_flow": PLANNED_FLOW,
        })

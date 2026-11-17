from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.audit.services import log_action
from apps.common.audit_mixin import AuditedModelViewSet
from apps.common.permissions import ActionPermission

from .serializers import (
    ChangePasswordSerializer, LoginSerializer, LogoutSerializer, MeSerializer,
    ProfileUpdateSerializer, UserReadSerializer, UserWriteSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    """Inicio de sesión. Devuelve access, refresh y el usuario autenticado."""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        username = str(request.data.get("username", ""))[:150]
        try:
            response = super().post(request, *args, **kwargs)
        except Exception:
            log_action(request, "LOGIN_FAILED", entity_type="auth", changes={"username": username})
            raise
        user = User.objects.filter(username=username).first()
        log_action(request, "LOGIN", user, actor=user)
        return response


class LogoutView(APIView):
    """Cierre de sesión: invalida (lista negra) el refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Token inválido o ya utilizado."}, status=status.HTTP_400_BAD_REQUEST)
        log_action(request, "LOGOUT", request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """Usuario autenticado: consulta y edición de datos básicos del propio perfil."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(request, "PROFILE_UPDATE", request.user)
        return Response(MeSerializer(request.user, context={"request": request}).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password", "updated_at"])
        log_action(request, "PASSWORD_CHANGE", request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(AuditedModelViewSet):
    """CRUD de usuarios. DELETE desactiva la cuenta."""

    queryset = User.objects.prefetch_related("roles", "extra_permissions")
    permission_classes = [ActionPermission]
    permission_map = {
        "list": "users.view",
        "retrieve": "users.view",
        "create": "users.manage",
        "update": "users.manage",
        "partial_update": "users.manage",
        "destroy": "users.manage",
    }
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name", "document_number"]
    ordering_fields = ["username", "last_name", "date_joined", "last_login"]

    def get_serializer_class(self):
        return UserReadSerializer if self.action in ("list", "retrieve") else UserWriteSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("office"):
            qs = qs.filter(assignments__office_id=params["office"], assignments__is_active=True).distinct()
        if params.get("is_active") in ("true", "false"):
            qs = qs.filter(is_active=params["is_active"] == "true")
        return qs

    def get_audit_extra(self, instance):
        return {
            "roles": sorted(r.code for r in instance.roles.all()),
            "extra_permissions": sorted(p.code for p in instance.extra_permissions.all()),
        }

    def before_deactivate(self, instance):
        if instance.pk == self.request.user.pk:
            raise serializers.ValidationError("No puede desactivar su propia cuenta.")
        if instance.is_superuser and not self.request.user.is_superuser:
            raise serializers.ValidationError("Solo un superusuario puede desactivar a otro superusuario.")

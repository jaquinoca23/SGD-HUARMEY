from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio.")
        user = self.model(username=username, email=self.normalize_email(email), **extra)
        user.set_password(password)  # hash seguro de Django
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra)

    def create_superuser(self, username, email=None, password=None, **extra):
        extra["is_staff"] = True
        extra["is_superuser"] = True
        return self._create_user(username, email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Usuario del sistema. La oficina, el cargo y el nivel de acceso viven en
    organization.Assignment; los roles y permisos en la app permissions."""

    username = models.CharField(
        "usuario", max_length=150, unique=True, validators=[UnicodeUsernameValidator()]
    )
    email = models.EmailField("correo electrónico", unique=True)
    first_name = models.CharField("nombres", max_length=150)
    last_name = models.CharField("apellidos", max_length=150)
    document_number = models.CharField("DNI / documento", max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField("teléfono", max_length=30, blank=True)
    is_active = models.BooleanField("activo", default=True)
    is_staff = models.BooleanField("acceso a /admin de Django", default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    class Meta:
        ordering = ["last_name", "first_name", "username"]
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.first_name or self.username

    def __str__(self):
        return f"{self.username} ({self.full_name})"

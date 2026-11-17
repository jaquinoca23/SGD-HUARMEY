import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateFileStorage(FileSystemStorage):
    """Almacenamiento fuera de cualquier URL pública. Lee PRIVATE_MEDIA_ROOT en cada uso
    (así las pruebas pueden redirigirlo con override_settings)."""

    def __init__(self):
        super().__init__(location=None, base_url=None)

    @property
    def base_location(self):
        return str(settings.PRIVATE_MEDIA_ROOT)

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):
        return None

    @base_url.setter
    def base_url(self, value):
        pass

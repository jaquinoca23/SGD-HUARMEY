from django.apps import AppConfig


class TemplatesConfig(AppConfig):
    name = "apps.templates"
    label = "doc_templates"  # evita confundirse con el concepto TEMPLATES de Django
    verbose_name = "Plantillas documentales"

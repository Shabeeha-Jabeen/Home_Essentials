# adminpanel/apps.py
from django.apps import AppConfig

class AdminpanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adminpanel'

    def ready(self):
        import adminpanel.signals  # സിഗ്നൽ കണക്ട് ചെയ്യുന്നു
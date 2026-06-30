"""
Accounts app configuration.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'

    def ready(self):
        """Import signals when the app is ready."""
        # Import signals here if needed
        pass

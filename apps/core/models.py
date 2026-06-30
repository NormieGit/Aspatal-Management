"""
Abstract base model with common fields for all models.
"""
from django.db import models


class AbstractBaseModel(models.Model):
    """
    Abstract base model with created_at and updated_at timestamps.
    All models should inherit from this to ensure consistent auditing.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True

    def get_changes(self, new_data: dict) -> dict:
        """
        Compare current instance with new data and return changed fields.
        Used for audit logging.
        """
        changes = {}
        for field_name, new_value in new_data.items():
            if hasattr(self, field_name):
                old_value = getattr(self, field_name)
                if old_value != new_value:
                    changes[field_name] = {
                        'old': str(old_value),
                        'new': str(new_value)
                    }
        return changes

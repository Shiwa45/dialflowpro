"""
Common models - Base classes used across all apps.
Replaces django_lets_go.intermediate_model_base_class.Model
"""
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model with created_date and updated_date.
    Replaces django_lets_go.intermediate_model_base_class.Model from original system.
    
    All models should inherit from this instead of models.Model directly.
    """
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True
        get_latest_by = 'created_date'
        ordering = ['-created_date']

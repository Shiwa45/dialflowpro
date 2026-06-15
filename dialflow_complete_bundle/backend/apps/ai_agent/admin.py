"""Minimal Django admin (project uses React UI; this is for support/debug)."""
from django.contrib import admin
from .models import (
    AISubscription, AIAgent, AIKnowledgeItem, AICallSession, AICallback,
)

admin.site.register(AISubscription)
admin.site.register(AIAgent)
admin.site.register(AIKnowledgeItem)
admin.site.register(AICallSession)
admin.site.register(AICallback)

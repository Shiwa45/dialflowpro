"""URL patterns for the AI Agent app (Phase 2: worker endpoints added)."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import worker_api

app_name = "ai_agent"

router = DefaultRouter()
router.register(r"agents", views.AIAgentViewSet, basename="ai-agent")
router.register(r"knowledge", views.AIKnowledgeItemViewSet, basename="ai-knowledge")
router.register(r"sessions", views.AICallSessionViewSet, basename="ai-session")
router.register(r"callbacks", views.AICallbackViewSet, basename="ai-callback")
router.register(r"subscription", views.AISubscriptionView, basename="ai-subscription")

urlpatterns = [
    path("", include(router.urls)),
    # Worker-facing (shared-secret auth, no user session)
    path("worker/config/", worker_api.worker_agent_config, name="worker-config"),
    path("worker/retrieve/", worker_api.worker_retrieve, name="worker-retrieve"),
    path("worker/result/", worker_api.worker_call_result, name="worker-result"),
    path("worker/callback/", worker_api.worker_schedule_callback, name="worker-callback"),
]

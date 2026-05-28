"""URL patterns for survey"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'survey'

router = DefaultRouter()
router.register(r'surveys', views.SurveyViewSet, basename='survey')
router.register(r'sections', views.SurveySectionViewSet, basename='section')
router.register(r'branches', views.SurveyBranchViewSet, basename='branch')
router.register(r'responses', views.SurveyResponseViewSet, basename='response')

urlpatterns = [
    path('', include(router.urls)),
]

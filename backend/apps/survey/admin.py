"""Django admin for Survey"""
from django.contrib import admin
from .models import Survey, SurveySection, SurveyBranch, SurveyResponse


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'user', 'campaign_count', 'created_date']
    list_filter = ['status', 'created_date']
    search_fields = ['name', 'user__username']
    readonly_fields = ['campaign_count', 'created_date', 'updated_date']


@admin.register(SurveySection)
class SurveySectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'survey', 'section_type', 'order']
    list_filter = ['section_type', 'survey']
    search_fields = ['name', 'survey__name']
    readonly_fields = ['created_date', 'updated_date']


@admin.register(SurveyBranch)
class SurveyBranchAdmin(admin.ModelAdmin):
    list_display = ['section', 'key_value', 'goto_section']
    list_filter = ['section__survey']
    raw_id_fields = ['section', 'goto_section']


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['survey', 'callrequest', 'completed', 'created_date']
    list_filter = ['completed', 'created_date']
    readonly_fields = ['created_date', 'updated_date']
    raw_id_fields = ['survey', 'callrequest']

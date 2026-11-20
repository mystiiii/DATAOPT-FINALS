from django.contrib import admin
from .models import SavedReportPreset, ReportAnnotation, DataQualityLog, AuditLog


@admin.register(SavedReportPreset)
class SavedReportPresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'module', 'created_by', 'created_at', 'updated_at')
    list_filter = ('module',)
    search_fields = ('name', 'created_by__username')


@admin.register(ReportAnnotation)
class ReportAnnotationAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'author', 'created_at', 'updated_at')
    list_filter = ('module',)
    search_fields = ('title', 'content', 'author__username')


@admin.register(DataQualityLog)
class DataQualityLogAdmin(admin.ModelAdmin):
    list_display = ('issue_title', 'severity', 'affected_tables', 'created_at')
    list_filter = ('severity',)
    search_fields = ('issue_title', 'affected_tables', 'impact_description')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'username_snapshot', 'role_snapshot', 'action', 'module', 'target_type', 'target_id')
    list_filter = ('action', 'role_snapshot', 'module')
    search_fields = ('username_snapshot', 'target_type', 'details')
    readonly_fields = ('user', 'username_snapshot', 'role_snapshot', 'action', 'module', 'target_type', 'target_id', 'details', 'created_at')

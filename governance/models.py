from django.db import models
from django.contrib.auth.models import User

class SavedReportPreset(models.Model):
    MODULE_CHOICES = [
        ('sales', 'Sales Report'),
        ('customers', 'Customer Profile'),
        ('revenue_loss', 'Revenue and Loss'),
        ('cost', 'Cost Report'),
    ]

    name = models.CharField(max_length=150)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    filter_params = models.JSONField(default=dict, help_text="Stored filter state (dates, categories, territories)")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_presets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_module_display()}) by {self.created_by.username}"

class ReportAnnotation(models.Model):
    module = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annotations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.author.username}"

class DataQualityLog(models.Model):
    SEVERITY_CHOICES = [
        ('INFO', 'Informational'),
        ('MEDIUM', 'Medium Limitation'),
        ('HIGH', 'High Critical Impact'),
    ]

    issue_title = models.CharField(max_length=200)
    affected_tables = models.CharField(max_length=200)
    evidence_query = models.TextField()
    impact_description = models.TextField()
    handling_strategy = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.severity}] {self.issue_title}"

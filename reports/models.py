# Simplified reports models - keeping only essential models for future use
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ReportLog(models.Model):
    """Log of generated reports"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    parameters = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.report_name} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Report Log"
        verbose_name_plural = "Report Logs"
        ordering = ['-generated_at']

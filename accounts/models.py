from django.db import models
from django.contrib.auth.models import User

class Role(models.TextChoices):
    ADMINISTRATOR = 'Administrator', 'Administrator'
    MANAGER = 'Manager', 'Manager'
    SUPERVISOR = 'Supervisor', 'Supervisor'
    EMPLOYEE = 'Employee', 'Employee'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    department = models.CharField(max_length=100, blank=True, default='General')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_administrator(self):
        return self.role == Role.ADMINISTRATOR or self.user.is_superuser

    @property
    def is_manager(self):
        return self.role in [Role.ADMINISTRATOR, Role.MANAGER] or self.user.is_superuser

    @property
    def is_supervisor(self):
        return self.role in [Role.ADMINISTRATOR, Role.MANAGER, Role.SUPERVISOR] or self.user.is_superuser

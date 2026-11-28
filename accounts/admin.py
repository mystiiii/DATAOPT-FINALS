from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'color_scheme')
    list_filter = ('role', 'department', 'color_scheme')
    search_fields = ('user__username', 'user__email', 'department')

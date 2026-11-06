from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from .models import Role

def role_required(allowed_roles):
    """
    Decorator to ensure user has one of the allowed roles.
    Superusers automatically bypass role checks.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            profile = getattr(request.user, 'profile', None)
            if not profile or profile.role not in allowed_roles:
                raise PermissionDenied("You do not have permission to access this reporting resource.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

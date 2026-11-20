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
                from governance.models import log_audit_event
                log_audit_event(
                    user=request.user,
                    action='ACCESS_DENIED',
                    target_type='Route',
                    target_id=request.path,
                    module=request.resolver_match.url_name if request.resolver_match else '',
                    details=f"Role '{profile.role if profile else 'None'}' attempted to access restricted path {request.path}"
                )
                raise PermissionDenied("You do not have permission to access this reporting resource.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

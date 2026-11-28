from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from accounts.decorators import role_required
from accounts.models import Role
from .models import AuditLog


@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER, Role.SUPERVISOR])
def audit_log_view(request):
    action_filter = request.GET.get('action', 'all')
    module_filter = request.GET.get('module', 'all')
    search_q = request.GET.get('q', '').strip()

    profile = getattr(request.user, 'profile', None)
    is_admin = bool(request.user.is_superuser or (profile and profile.is_administrator))
    is_manager = bool(profile and profile.role == Role.MANAGER)

    logs = AuditLog.objects.all()
    if is_admin:
        audit_scope_label = 'All roles'
    elif is_manager:
        logs = logs.filter(role_snapshot__in=[Role.MANAGER, Role.SUPERVISOR, Role.EMPLOYEE])
        audit_scope_label = 'Managers, Supervisors & Employees'
    else:
        logs = logs.filter(role_snapshot__in=[Role.SUPERVISOR, Role.EMPLOYEE])
        audit_scope_label = 'Supervisors & Employees'

    if action_filter != 'all':
        logs = logs.filter(action=action_filter)
    if module_filter != 'all':
        logs = logs.filter(module=module_filter)
    if search_q:
        logs = logs.filter(
            Q(details__icontains=search_q)
            | Q(username_snapshot__icontains=search_q)
            | Q(target_type__icontains=search_q)
            | Q(module__icontains=search_q)
        )

    logs = list(logs[:150])

    return render(request, 'governance/audit_log.html', {
        'logs': logs,
        'action_filter': action_filter,
        'module_filter': module_filter,
        'search_q': search_q,
        'audit_scope_label': audit_scope_label,
    })

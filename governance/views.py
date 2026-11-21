from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from accounts.decorators import role_required
from accounts.models import Role
from .models import AuditLog, DataQualityLog


@login_required
@role_required([Role.ADMINISTRATOR])
def audit_log_view(request):
    action_filter = request.GET.get('action', 'all')
    module_filter = request.GET.get('module', 'all')
    search_q = request.GET.get('q', '').strip()

    logs = AuditLog.objects.all()
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
    data_quality_logs = DataQualityLog.objects.all()

    return render(request, 'governance/audit_log.html', {
        'logs': logs,
        'data_quality_logs': data_quality_logs,
        'action_filter': action_filter,
        'module_filter': module_filter,
        'search_q': search_q,
        'total_events': AuditLog.objects.count(),
        'view_events': AuditLog.objects.filter(action='VIEW').count(),
        'denied_events': AuditLog.objects.filter(action='ACCESS_DENIED').count(),
    })

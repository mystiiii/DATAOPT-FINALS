import json
import re
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from governance.models import log_audit_event
from .decorators import role_required
from .models import UserProfile, Role, ColorScheme


def _sync_user_role_and_group(target_user, role_value, department_value):
    if role_value not in Role.values:
        role_value = Role.EMPLOYEE
    group, _ = Group.objects.get_or_create(name=role_value)
    target_user.groups.clear()
    target_user.groups.add(group)

    is_admin_role = (role_value == Role.ADMINISTRATOR)
    target_user.is_staff = is_admin_role
    target_user.is_superuser = is_admin_role
    target_user.save()

    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    profile.role = role_value
    profile.department = department_value or 'General'
    profile.save()
    return profile


def _record_django_admin_log(actor, target_user, action_flag, change_message):
    try:
        ct = ContentType.objects.get_for_model(User)
        LogEntry.objects.log_action(
            user_id=actor.pk,
            content_type_id=ct.pk,
            object_id=target_user.pk,
            object_repr=str(target_user),
            action_flag=action_flag,
            change_message=change_message,
        )
    except Exception:
        pass


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            log_audit_event(
                user, 'LOGIN', 'Session',
                module='auth',
                details=f"Signed in from {request.META.get('REMOTE_ADDR', 'local')}."
            )
            next_url = request.POST.get('next') or request.GET.get('next') or ''
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        log_audit_event(
            request.user, 'LOGOUT', 'Session',
            module='auth',
            details="Signed out."
        )
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
@role_required([Role.ADMINISTRATOR])
def user_management_view(request):
    role_filter = request.GET.get('role', 'all').strip()
    status_filter = request.GET.get('status', 'all').strip()
    search_q = request.GET.get('q', '').strip()

    for r in Role.values:
        Group.objects.get_or_create(name=r)

    users_qs = User.objects.select_related('profile').prefetch_related('groups').order_by('id')
    for u in users_qs:
        if not hasattr(u, 'profile'):
            default_role = Role.ADMINISTRATOR if u.is_superuser else Role.EMPLOYEE
            UserProfile.objects.create(user=u, role=default_role, department='General')

    users_qs = User.objects.select_related('profile').prefetch_related('groups').order_by('id')
    if role_filter != 'all' and role_filter in Role.values:
        users_qs = users_qs.filter(profile__role=role_filter)
    if status_filter == 'active':
        users_qs = users_qs.filter(is_active=True)
    elif status_filter == 'inactive':
        users_qs = users_qs.filter(is_active=False)
    if search_q:
        users_qs = users_qs.filter(
            Q(username__icontains=search_q)
            | Q(email__icontains=search_q)
            | Q(first_name__icontains=search_q)
            | Q(last_name__icontains=search_q)
            | Q(profile__department__icontains=search_q)
        )

    all_users = User.objects.select_related('profile').all()
    total_users = all_users.count()
    active_users = all_users.filter(is_active=True).count()
    admin_count = all_users.filter(Q(profile__role=Role.ADMINISTRATOR) | Q(is_superuser=True)).distinct().count()
    role_counts = {
        r_label: all_users.filter(profile__role=r_val).count()
        for r_val, r_label in Role.choices
    }

    ct = ContentType.objects.get_for_model(User)
    admin_logs = LogEntry.objects.filter(content_type=ct).select_related('user').order_by('-action_time')[:20]

    log_audit_event(
        request.user, 'VIEW', 'UserManagement',
        target_id=request.path,
        module='auth',
        details="Accessed Users & Roles Administration UI."
    )

    return render(request, 'accounts/user_management.html', {
        'users_list': users_qs,
        'roles': Role.choices,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_q': search_q,
        'total_users': total_users,
        'active_users': active_users,
        'admin_count': admin_count,
        'role_counts': role_counts,
        'admin_logs': admin_logs,
    })


@login_required
@role_required([Role.ADMINISTRATOR])
@require_POST
def create_user_view(request):
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    password = request.POST.get('password', '').strip()
    role_value = request.POST.get('role', Role.EMPLOYEE).strip()
    department = request.POST.get('department', 'General').strip() or 'General'
    is_active = request.POST.get('is_active', '1') == '1'

    if not username or not password:
        messages.error(request, "Username and password are required to create a user.")
        return redirect('user_management')

    if User.objects.filter(username__iexact=username).exists():
        messages.error(request, f"Username '{username}' already exists.")
        return redirect('user_management')

    new_user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
    )
    _sync_user_role_and_group(new_user, role_value, department)

    msg = f"Created user '{new_user.username}' with role '{role_value}' ({department})."
    _record_django_admin_log(request.user, new_user, ADDITION, msg)
    log_audit_event(
        request.user, 'CREATE', 'User',
        target_id=new_user.pk,
        module='auth',
        details=msg,
    )
    messages.success(request, f"Created user '{new_user.username}' ({role_value}).")
    return redirect('user_management')


@login_required
@role_required([Role.ADMINISTRATOR])
@require_POST
def edit_user_view(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    username = request.POST.get('username', '').strip() or target_user.username
    email = request.POST.get('email', '').strip()
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    role_value = request.POST.get('role', Role.EMPLOYEE).strip()
    department = request.POST.get('department', 'General').strip() or 'General'
    new_password = request.POST.get('password', '').strip()
    is_active = request.POST.get('is_active') == '1'

    if User.objects.filter(username__iexact=username).exclude(pk=target_user.pk).exists():
        messages.error(request, f"Another account already uses the username '{username}'.")
        return redirect('user_management')

    if target_user.pk == request.user.pk:
        if not is_active:
            messages.error(request, "You cannot deactivate your own active administrator account.")
            return redirect('user_management')
        if role_value != Role.ADMINISTRATOR:
            messages.error(request, "You cannot demote your own administrator account.")
            return redirect('user_management')

    target_user.username = username
    target_user.email = email
    target_user.first_name = first_name
    target_user.last_name = last_name
    target_user.is_active = is_active
    if new_password:
        target_user.set_password(new_password)
    _sync_user_role_and_group(target_user, role_value, department)

    pw_note = " (password reset)" if new_password else ""
    status_note = "Active" if is_active else "Inactive"
    msg = f"Updated user '{target_user.username}': role={role_value}, dept={department}, status={status_note}{pw_note}."
    _record_django_admin_log(request.user, target_user, CHANGE, msg)
    log_audit_event(
        request.user, 'EDIT', 'User',
        target_id=target_user.pk,
        module='auth',
        details=msg,
    )
    messages.success(request, f"Updated user '{target_user.username}'.")
    return redirect('user_management')


@login_required
@role_required([Role.ADMINISTRATOR])
@require_POST
def delete_user_view(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    if target_user.pk == request.user.pk:
        messages.error(request, "You cannot delete your own signed-in administrator account.")
        return redirect('user_management')

    uname = target_user.username
    uid = target_user.pk
    role_val = getattr(getattr(target_user, 'profile', None), 'role', 'Unknown')
    msg = f"Deleted user '{uname}' (Role: {role_val})."
    _record_django_admin_log(request.user, target_user, DELETION, msg)
    target_user.delete()
    log_audit_event(
        request.user, 'DELETE', 'User',
        target_id=uid,
        module='auth',
        details=msg,
    )
    messages.success(request, f"Deleted user '{uname}'.")
    return redirect('user_management')


HEX_COLOR_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')

CUSTOM_COLOR_KEYS = (
    'accent',
    'canvas',
    'card',
    'text',
    'primary',
    'anchor',
    'positive',
    'secondary',
    'warning',
    'negative',
)

DEFAULT_CUSTOM_COLORS = {
    'accent': '#2F6396',
    'canvas': '#F5F7FA',
    'card': '#FFFFFF',
    'text': '#243447',
    'primary': '#4A89C7',
    'anchor': '#5B7FA6',
    'positive': '#3E9B8C',
    'secondary': '#7A7EC9',
    'warning': '#9A72B5',
    'negative': '#C9657B',
}


def _sanitize_custom_colors(raw_mapping):
    cleaned = {}
    if not isinstance(raw_mapping, dict):
        return cleaned
    for key in CUSTOM_COLOR_KEYS:
        val = raw_mapping.get(key)
        if isinstance(val, str):
            val = val.strip()
            if HEX_COLOR_RE.match(val):
                cleaned[key] = val.upper()
    return cleaned


def _get_or_create_profile(user):
    default_role = Role.ADMINISTRATOR if user.is_superuser else Role.EMPLOYEE
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': default_role, 'department': 'General'},
    )
    return profile


@login_required
def settings_view(request):
    """Settings tab accessible to all authenticated roles for personal color scheme customization."""
    profile = _get_or_create_profile(request.user)

    if request.method == 'POST':
        action = (request.POST.get('action') or 'save').strip()
        if action == 'reset':
            profile.color_scheme = ColorScheme.SLATE_BLUE
            profile.custom_colors = {}
            profile.save(update_fields=['color_scheme', 'custom_colors'])
            messages.success(request, 'Color scheme reset to Classic Slate default.')
            return redirect('settings')

        scheme = (request.POST.get('color_scheme') or ColorScheme.CUSTOM).strip()
        if scheme not in ColorScheme.values:
            messages.error(request, 'Invalid color scheme selection.')
            return redirect('settings')

        if scheme == ColorScheme.CUSTOM:
            raw_colors = {k: request.POST.get(f'color_{k}', '') for k in CUSTOM_COLOR_KEYS}
            cleaned = _sanitize_custom_colors(raw_colors)
            if not cleaned:
                messages.error(request, 'Please provide valid hex color values (e.g. #2F6396).')
                return redirect('settings')
            merged = dict(DEFAULT_CUSTOM_COLORS)
            merged.update(cleaned)
            profile.color_scheme = ColorScheme.CUSTOM
            profile.custom_colors = merged
        else:
            profile.color_scheme = scheme
            profile.custom_colors = {}

        profile.save(update_fields=['color_scheme', 'custom_colors'])
        messages.success(request, 'Your color scheme preferences have been saved.')
        return redirect('settings')

    effective_custom = dict(DEFAULT_CUSTOM_COLORS)
    if isinstance(profile.custom_colors, dict):
        effective_custom.update(_sanitize_custom_colors(profile.custom_colors))

    return render(request, 'accounts/settings.html', {
        'profile': profile,
        'effective_custom_colors': effective_custom,
    })


@login_required
@require_POST
def update_color_scheme_view(request):
    """Allow any authenticated user (all roles) to save a preset or custom color scheme via AJAX or POST."""
    scheme = ''
    raw_custom = {}
    if request.content_type and 'application/json' in request.content_type:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
            scheme = str(payload.get('scheme') or '').strip()
            raw_custom = payload.get('custom_colors') or {}
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'ok': False, 'error': 'Invalid JSON payload.'}, status=400)
    else:
        scheme = str(request.POST.get('scheme') or '').strip()
        raw_custom = {k: request.POST.get(f'color_{k}', '') for k in CUSTOM_COLOR_KEYS if request.POST.get(f'color_{k}')}

    if scheme not in ColorScheme.values:
        return JsonResponse({'ok': False, 'error': 'Unsupported color scheme.'}, status=400)

    profile = _get_or_create_profile(request.user)
    if scheme == ColorScheme.CUSTOM:
        cleaned = _sanitize_custom_colors(raw_custom)
        if not cleaned:
            return JsonResponse({'ok': False, 'error': 'Provide at least one valid hex color.'}, status=400)
        merged = dict(DEFAULT_CUSTOM_COLORS)
        merged.update(cleaned)
        profile.color_scheme = ColorScheme.CUSTOM
        profile.custom_colors = merged
    else:
        profile.color_scheme = scheme
        profile.custom_colors = {}

    profile.save(update_fields=['color_scheme', 'custom_colors'])
    return JsonResponse({
        'ok': True,
        'color_scheme': profile.color_scheme,
        'custom_colors': profile.custom_colors,
    })

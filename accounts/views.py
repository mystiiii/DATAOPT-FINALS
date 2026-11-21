from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from governance.models import log_audit_event
from .models import UserProfile, Role

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

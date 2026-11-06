from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import role_required
from accounts.models import Role
from governance.models import SavedReportPreset, DataQualityLog
from .services import sales_service, customer_service, revenue_loss_service, cost_service

@login_required
def dashboard_view(request):
    profile = getattr(request.user, 'profile', None)
    scrap_list = revenue_loss_service.get_production_scrap_loss() or []
    vendor_list = cost_service.get_vendor_purchasing_spend(1) or []
    customer_types = customer_service.get_customer_type_breakdown() or []
    revenue_data = revenue_loss_service.get_revenue_and_loss_by_year() or []

    context = {
        'role': profile.role if profile else 'Employee',
        'sales_preview': sales_service.get_sales_by_category_and_year()[:4],
        'top_customers': customer_service.get_top_customers(5),
        'revenue_summary': revenue_data[-1] if revenue_data else {},
        'scrap_preview': scrap_list[0] if scrap_list else {},
        'vendor_preview': vendor_list[0] if vendor_list else {},
        'customer_types': customer_types,
        'data_issues': DataQualityLog.objects.all()[:3],
    }
    return render(request, 'reports/dashboard.html', context)

@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER, Role.SUPERVISOR, Role.EMPLOYEE])
def sales_report_view(request):
    sales_data = sales_service.get_sales_by_category_and_year()
    top_products = sales_service.get_top_selling_products(10)
    presets = SavedReportPreset.objects.filter(module='sales')
    return render(request, 'reports/sales.html', {
        'sales_data': sales_data,
        'top_products': top_products,
        'presets': presets,
    })

@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER, Role.SUPERVISOR, Role.EMPLOYEE])
def customer_report_view(request):
    top_customers = customer_service.get_top_customers(10)
    customer_types = customer_service.get_customer_type_breakdown()
    presets = SavedReportPreset.objects.filter(module='customers')
    return render(request, 'reports/customers.html', {
        'top_customers': top_customers,
        'customer_types': customer_types,
        'presets': presets,
    })

@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER])
def revenue_loss_report_view(request):
    revenue_data = revenue_loss_service.get_revenue_and_loss_by_year()
    scrap_data = revenue_loss_service.get_production_scrap_loss()
    presets = SavedReportPreset.objects.filter(module='revenue_loss')
    return render(request, 'reports/revenue_loss.html', {
        'revenue_data': revenue_data,
        'scrap_data': scrap_data,
        'presets': presets,
    })

@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER])
def cost_report_view(request):
    margins = cost_service.get_product_margins(15)
    vendor_spend = cost_service.get_vendor_purchasing_spend(10)
    presets = SavedReportPreset.objects.filter(module='cost')
    return render(request, 'reports/cost.html', {
        'margins': margins,
        'vendor_spend': vendor_spend,
        'presets': presets,
    })

@login_required
def save_preset_view(request):
    """
    Allows users to save a custom filter preset (View/Edit/Delete scope).
    """
    if request.method == 'POST':
        name = request.POST.get('name', 'My Saved Filter')
        module = request.POST.get('module', 'sales')
        preset = SavedReportPreset.objects.create(
            name=name,
            module=module,
            filter_params={'filter': request.POST.get('filter_param', 'all')},
            created_by=request.user
        )
        messages.success(request, f"Saved preset '{preset.name}' successfully.")
        return redirect(f'report_{module}')
    return redirect('dashboard')

@login_required
def delete_preset_view(request, preset_id):
    preset = get_object_or_404(SavedReportPreset, id=preset_id)
    profile = getattr(request.user, 'profile', None)
    
    # Permission check: Owner or Manager/Admin
    if preset.created_by == request.user or (profile and profile.is_manager):
        module = preset.module
        preset.delete()
        messages.success(request, f"Preset '{preset.name}' deleted.")
        return redirect(f'report_{module}')
    else:
        messages.error(request, "Permission denied: you cannot delete this preset.")
        return redirect('dashboard')

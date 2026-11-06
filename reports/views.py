import json
from decimal import Decimal
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import role_required
from accounts.models import Role
from governance.models import SavedReportPreset, DataQualityLog
from .services import sales_service, customer_service, revenue_loss_service, cost_service
from .services.db_helper import DatabaseConnectionError

def serialize_for_json(data):
    def default(o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return str(o)
    return json.dumps(data, default=default)

@login_required
def dashboard_view(request):
    profile = getattr(request.user, 'profile', None)
    db_error = None
    
    try:
        scrap_list = revenue_loss_service.get_production_scrap_loss() or []
        vendor_list = cost_service.get_vendor_purchasing_spend(1) or []
        customer_types = customer_service.get_customer_type_breakdown() or []
        revenue_data = revenue_loss_service.get_revenue_and_loss_by_year() or []
        sales_preview = sales_service.get_sales_by_category_and_year() or []
        top_customers = customer_service.get_top_customers(5) or []

        total_scrapped_qty = sum(item.get('TotalScrappedQty', 0) for item in scrap_list)
        total_scrap_loss = int(total_scrapped_qty * 36.50) if total_scrapped_qty else 0
        total_orders = sum(item.get('OrderCount', 0) for item in revenue_data)
        total_gross = sum(item.get('GrossAmount', 0) for item in revenue_data)
        total_net = sum(item.get('NetRevenue', 0) for item in revenue_data)
        avg_order = (float(total_gross) / total_orders) if total_orders else 0

        b2b_rev, b2c_rev = 0, 0
        for ct in customer_types:
            ctype = ct.get('CustomerType', '')
            if 'Store' in ctype or 'B2B' in ctype:
                b2b_rev += float(ct.get('TotalRevenue', 0))
            else:
                b2c_rev += float(ct.get('TotalRevenue', 0))
        tot_cust_rev = b2b_rev + b2c_rev
        b2b_pct = round((b2b_rev / tot_cust_rev * 100), 1) if tot_cust_rev else 68.0
        b2c_pct = round((b2c_rev / tot_cust_rev * 100), 1) if tot_cust_rev else 32.0

        revenue_summary = revenue_data[-1] if revenue_data else {}
        scrap_preview = scrap_list[0] if scrap_list else {}
        vendor_preview = vendor_list[0] if vendor_list else {}
    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")
        scrap_list, vendor_list, customer_types, revenue_data, sales_preview, top_customers = [], [], [], [], [], []
        total_scrap_loss = 0
        total_orders, total_gross, total_net, avg_order = 0, 0, 0, 0
        b2b_rev, b2c_rev, b2b_pct, b2c_pct = 0, 0, 0, 0
        revenue_summary, scrap_preview, vendor_preview = {}, {}, {}

    context = {
        'role': profile.role if profile else 'Employee',
        'sales_preview': sales_preview[:4],
        'top_customers': top_customers,
        'revenue_summary': revenue_summary,
        'revenue_data': revenue_data,
        'revenue_data_json': serialize_for_json(revenue_data),
        'total_orders': total_orders,
        'total_gross': total_gross,
        'total_net': total_net,
        'avg_order': avg_order,
        'b2b_rev': b2b_rev,
        'b2c_rev': b2c_rev,
        'b2b_pct': b2b_pct,
        'b2c_pct': b2c_pct,
        'scrap_preview': scrap_preview,
        'total_scrap_loss': total_scrap_loss,
        'vendor_preview': vendor_preview,
        'customer_types': customer_types,
        'data_issues': DataQualityLog.objects.all()[:3],
        'db_error': db_error,
    }
    return render(request, 'reports/dashboard.html', context)

@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER, Role.SUPERVISOR, Role.EMPLOYEE])
def sales_report_view(request):
    db_error = None
    try:
        sales_data = sales_service.get_sales_by_category_and_year() or []
        top_products = sales_service.get_top_selling_products(10) or []
        territory_sales = sales_service.get_territory_sales() or []
    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")
        sales_data, top_products, territory_sales = [], [], []

    presets = SavedReportPreset.objects.filter(module='sales')
    return render(request, 'reports/sales.html', {
        'sales_data': sales_data,
        'sales_data_json': serialize_for_json(sales_data),
        'top_products': top_products,
        'territory_sales': territory_sales,
        'territory_sales_json': serialize_for_json(territory_sales),
        'presets': presets,
        'db_error': db_error,
    })

@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER, Role.SUPERVISOR, Role.EMPLOYEE])
def customer_report_view(request):
    db_error = None
    try:
        top_customers = customer_service.get_top_customers(10) or []
        customer_types = customer_service.get_customer_type_breakdown() or []
        geo_distribution = customer_service.get_customer_geographic_distribution() or []
    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")
        top_customers, customer_types, geo_distribution = [], [], []

    presets = SavedReportPreset.objects.filter(module='customers')
    return render(request, 'reports/customers.html', {
        'top_customers': top_customers,
        'customer_types': customer_types,
        'customer_types_json': serialize_for_json(customer_types),
        'geo_distribution': geo_distribution,
        'geo_distribution_json': serialize_for_json(geo_distribution),
        'presets': presets,
        'db_error': db_error,
    })

@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER])
def revenue_loss_report_view(request):
    db_error = None
    try:
        revenue_data = revenue_loss_service.get_revenue_and_loss_by_year() or []
        scrap_data = revenue_loss_service.get_production_scrap_loss() or []
    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")
        revenue_data, scrap_data = [], []

    presets = SavedReportPreset.objects.filter(module='revenue_loss')
    return render(request, 'reports/revenue_loss.html', {
        'revenue_data': revenue_data,
        'revenue_data_json': serialize_for_json(revenue_data),
        'scrap_data': scrap_data,
        'scrap_data_json': serialize_for_json(scrap_data),
        'presets': presets,
        'db_error': db_error,
    })

@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER])
def cost_report_view(request):
    db_error = None
    try:
        margins = cost_service.get_product_margins(15) or []
        vendor_spend = cost_service.get_vendor_purchasing_spend(10) or []
        cost_history = cost_service.get_standard_cost_history() or []
    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")
        margins, vendor_spend, cost_history = [], [], []

    presets = SavedReportPreset.objects.filter(module='cost')
    return render(request, 'reports/cost.html', {
        'margins': margins,
        'vendor_spend': vendor_spend,
        'vendor_spend_json': serialize_for_json(vendor_spend),
        'cost_history': cost_history,
        'cost_history_json': serialize_for_json(cost_history),
        'presets': presets,
        'db_error': db_error,
    })

@login_required
def save_preset_view(request):
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
    
    if preset.created_by == request.user or (profile and profile.is_manager):
        module = preset.module
        preset.delete()
        messages.success(request, f"Preset '{preset.name}' deleted.")
        return redirect(f'report_{module}')
    else:
        messages.error(request, "Permission denied: you cannot delete this preset.")
        return redirect('dashboard')

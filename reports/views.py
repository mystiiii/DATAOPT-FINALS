import json
from decimal import Decimal
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from accounts.decorators import role_required
from accounts.models import Role
from governance.models import SavedReportPreset, ReportAnnotation, DataQualityLog, log_audit_event
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


def _get_role_context(user):
    profile = getattr(user, 'profile', None)
    role = profile.role if profile else ('Administrator' if user.is_superuser else Role.EMPLOYEE)
    is_admin = bool(user.is_superuser or (profile and profile.is_administrator))
    is_manager = bool(user.is_superuser or (profile and profile.is_manager))
    is_supervisor = bool(user.is_superuser or (profile and profile.is_supervisor))
    return {
        'role': role,
        'is_admin': is_admin,
        'is_manager': is_manager,
        'is_supervisor': is_supervisor,
        'can_edit_governance': is_supervisor,
    }


def _allowed_modules_for_user(user):
    ctx = _get_role_context(user)
    if ctx['is_manager']:
        return {'sales', 'customers', 'revenue_loss', 'cost'}
    if ctx['is_supervisor']:
        return {'sales', 'customers'}
    return set()


def _strip_fields(rows, fields_to_remove):
    return [{k: v for k, v in row.items() if k not in fields_to_remove} for row in (rows or [])]


def _require_governance_access(request, module, obj_owner=None):
    ctx = _get_role_context(request.user)
    allowed = _allowed_modules_for_user(request.user)
    if not ctx['can_edit_governance'] or module not in allowed:
        log_audit_event(
            request.user, 'ACCESS_DENIED', 'Governance',
            module=module,
            details=f"Role '{ctx['role']}' attempted governance mutation on module '{module}'."
        )
        raise PermissionDenied("You do not have permission to modify governance records for this module.")
    if obj_owner is not None and obj_owner != request.user and not ctx['is_manager']:
        log_audit_event(
            request.user, 'ACCESS_DENIED', 'Governance',
            module=module,
            details=f"Role '{ctx['role']}' attempted to modify record owned by '{obj_owner.username}'."
        )
        raise PermissionDenied("You can only edit or delete your own saved items.")


@login_required
def dashboard_view(request):
    role_ctx = _get_role_context(request.user)
    is_manager = role_ctx['is_manager']
    is_supervisor = role_ctx['is_supervisor']
    db_error = None

    scrap_list, vendor_list, customer_types, revenue_data = [], [], [], []
    sales_by_cat_year, territory_sales, top_products, top_customers, monthly_trend = [], [], [], [], []
    total_scrap_loss, total_orders, total_units_sold = 0, 0, 0
    total_gross, total_discount, total_net, total_mfg_cost, total_real_profit, avg_order = 0, 0, 0, 0, 0, 0
    total_customers, b2b_rev, b2c_rev, b2b_pct, b2c_pct = 0, 0, 0, 0.0, 0.0
    revenue_summary, scrap_preview, vendor_preview = {}, {}, {}

    try:
        sales_by_cat_year = sales_service.get_sales_by_category_and_year() or []
        territory_sales = sales_service.get_territory_sales() or []
        top_products = sales_service.get_top_selling_products(50) or []
        monthly_trend = sales_service.get_monthly_sales_trend() or []

        if is_supervisor:
            customer_types = customer_service.get_customer_type_breakdown() or []
            top_customers = customer_service.get_top_customers(50) or []
            total_customers = sum(int(ct.get('ActiveBuyers') or ct.get('TotalCustomers') or 0) for ct in customer_types)
            for ct in customer_types:
                ctype = ct.get('CustomerType', '')
                if 'Store' in ctype or 'B2B' in ctype:
                    b2b_rev += float(ct.get('TotalRevenue', 0))
                else:
                    b2c_rev += float(ct.get('TotalRevenue', 0))
            tot_cust_rev = b2b_rev + b2c_rev
            b2b_pct = round((b2b_rev / tot_cust_rev * 100), 1) if tot_cust_rev else 0.0
            b2c_pct = round((b2c_rev / tot_cust_rev * 100), 1) if tot_cust_rev else 0.0

        if is_manager:
            scrap_list = revenue_loss_service.get_production_scrap_loss() or []
            vendor_list = cost_service.get_vendor_purchasing_spend(50) or []
            revenue_data = revenue_loss_service.get_revenue_and_loss_by_year() or []

            total_scrapped_qty = sum(item.get('TotalScrappedQty', 0) for item in scrap_list)
            actual_scrap_sum = sum(float(item.get('ActualScrapCost') or 0) for item in scrap_list)
            total_scrap_loss = int(round(actual_scrap_sum)) if actual_scrap_sum > 0 else (int(total_scrapped_qty * 36.50) if total_scrapped_qty else 0)
            total_orders = sum(item.get('OrderCount', 0) for item in revenue_data)
            total_gross = sum(float(item.get('GrossAmount', 0)) for item in revenue_data)
            total_discount = sum(float(item.get('DiscountLoss', 0)) for item in revenue_data)
            total_net = sum(float(item.get('NetRevenue', 0)) for item in revenue_data)
            total_mfg_cost = sum(float(item.get('ManufacturingCost', 0)) for item in sales_by_cat_year)
            total_real_profit = total_net - total_mfg_cost - total_scrap_loss
            avg_order = (total_gross / total_orders) if total_orders else 0
            revenue_summary = revenue_data[-1] if revenue_data else {}
            scrap_preview = scrap_list[0] if scrap_list else {}
            vendor_preview = vendor_list[0] if vendor_list else {}
        else:
            # Operational / Sales-only KPIs for Supervisor and Employee
            total_orders = sum(int(t.get('TotalOrders', 0)) for t in territory_sales)
            total_gross = sum(float(c.get('Revenue', 0)) for c in sales_by_cat_year)
            total_units_sold = sum(int(c.get('UnitsSold', 0)) for c in sales_by_cat_year)
            avg_order = (total_gross / total_orders) if total_orders else 0
            sales_by_cat_year = _strip_fields(sales_by_cat_year, {'ManufacturingCost', 'GrossProfit'})
            top_products = _strip_fields(top_products, {'TotalCost', 'MarginPercentage'})

    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")

    context = {
        **role_ctx,
        'sales_preview': sales_by_cat_year[:4],
        'top_customers': top_customers,
        'revenue_summary': revenue_summary,
        'revenue_data': revenue_data,
        'revenue_data_json': serialize_for_json(revenue_data),
        'sales_by_cat_year_json': serialize_for_json(sales_by_cat_year),
        'monthly_trend_json': serialize_for_json(monthly_trend),
        'territory_sales_json': serialize_for_json(territory_sales),
        'customer_types_json': serialize_for_json(customer_types),
        'top_products_json': serialize_for_json(top_products),
        'top_customers_json': serialize_for_json(top_customers),
        'scrap_list_json': serialize_for_json(scrap_list if is_manager else []),
        'vendor_list_json': serialize_for_json(vendor_list if is_manager else []),
        'total_orders': total_orders,
        'total_units_sold': total_units_sold,
        'total_gross': total_gross,
        'total_discount': total_discount,
        'total_net': total_net,
        'total_mfg_cost': total_mfg_cost,
        'total_real_profit': total_real_profit,
        'avg_order': avg_order,
        'total_customers': total_customers,
        'b2b_rev': b2b_rev,
        'b2c_rev': b2c_rev,
        'b2b_pct': b2b_pct,
        'b2c_pct': b2c_pct,
        'scrap_preview': scrap_preview,
        'total_scrap_loss': total_scrap_loss,
        'vendor_preview': vendor_preview,
        'customer_types': customer_types,
        'data_issues': DataQualityLog.objects.all()[:3] if is_manager else [],
        'db_error': db_error,
    }
    log_audit_event(
        request.user, 'VIEW', 'Dashboard',
        target_id=request.path,
        module='dashboard',
        details=f"Accessed Dashboard ({role_ctx['role']} view)."
    )
    return render(request, 'reports/dashboard.html', context)


@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER, Role.SUPERVISOR, Role.EMPLOYEE])
def sales_report_view(request):
    role_ctx = _get_role_context(request.user)
    is_manager = role_ctx['is_manager']
    db_error = None
    sales_data, monthly_trend, subcategories, top_products, low_products, territory_sales = [], [], [], [], [], []
    category_list = []

    try:
        sales_data = sales_service.get_sales_by_category_and_year() or []
        monthly_trend = sales_service.get_monthly_sales_trend() or []
        subcategories = sales_service.get_sales_by_subcategory(50) or []
        top_products = sales_service.get_top_selling_products(50) or []
        low_products = sales_service.get_low_performing_products(50) or []
        territory_sales = sales_service.get_territory_sales() or []

        category_summary = {}
        total_cat_rev = sum(float(item.get('Revenue', 0)) for item in sales_data)
        for item in sales_data:
            cat = item.get('Category')
            rev = float(item.get('Revenue', 0))
            units = int(item.get('UnitsSold', 0))
            if cat not in category_summary:
                category_summary[cat] = {'Category': cat, 'Revenue': 0.0, 'UnitsSold': 0}
            category_summary[cat]['Revenue'] += rev
            category_summary[cat]['UnitsSold'] += units

        category_list = sorted(category_summary.values(), key=lambda x: x['Revenue'], reverse=True)
        for c in category_list:
            c['Share'] = round((c['Revenue'] / total_cat_rev * 100), 1) if total_cat_rev else 0

        if not is_manager:
            sales_data = _strip_fields(sales_data, {'ManufacturingCost', 'GrossProfit'})
            top_products = _strip_fields(top_products, {'TotalCost', 'MarginPercentage'})
            low_products = _strip_fields(low_products, {'TotalCost', 'MarginPercentage'})
    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")

    log_audit_event(
        request.user, 'VIEW', 'Report',
        target_id=request.path,
        module='sales',
        details="Accessed Sales report."
    )
    presets = SavedReportPreset.objects.filter(module='sales').order_by('-updated_at')
    annotations = ReportAnnotation.objects.filter(module='sales').order_by('-updated_at')
    return render(request, 'reports/sales.html', {
        **role_ctx,
        'module': 'sales',
        'sales_data': sales_data,
        'category_list': category_list,
        'sales_data_json': serialize_for_json(sales_data),
        'monthly_trend_json': serialize_for_json(monthly_trend),
        'subcategories_json': serialize_for_json(subcategories),
        'top_products': top_products,
        'top_products_json': serialize_for_json(top_products),
        'low_products_json': serialize_for_json(low_products),
        'territory_sales': territory_sales,
        'territory_sales_json': serialize_for_json(territory_sales),
        'presets': presets,
        'annotations': annotations,
        'db_error': db_error,
    })


@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER, Role.SUPERVISOR])
def customer_report_view(request):
    role_ctx = _get_role_context(request.user)
    db_error = None
    top_customers, customer_types, geo_distribution = [], [], []
    country_geo, frequency_buckets, customer_trends = [], [], []

    try:
        top_customers = customer_service.get_top_customers(50) or []
        customer_types = customer_service.get_customer_type_breakdown() or []
        geo_distribution = customer_service.get_customer_geographic_distribution(50) or []
        country_geo = customer_service.get_country_customer_distribution() or []
        frequency_buckets = customer_service.get_purchase_frequency_buckets() or []
        customer_trends = customer_service.get_customer_trends_by_year() or []
    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")

    log_audit_event(
        request.user, 'VIEW', 'Report',
        target_id=request.path,
        module='customers',
        details="Accessed Customers report."
    )
    presets = SavedReportPreset.objects.filter(module='customers').order_by('-updated_at')
    annotations = ReportAnnotation.objects.filter(module='customers').order_by('-updated_at')
    return render(request, 'reports/customers.html', {
        **role_ctx,
        'module': 'customers',
        'top_customers': top_customers,
        'top_customers_json': serialize_for_json(top_customers),
        'customer_types': customer_types,
        'customer_types_json': serialize_for_json(customer_types),
        'geo_distribution': geo_distribution,
        'geo_distribution_json': serialize_for_json(geo_distribution),
        'country_geo_json': serialize_for_json(country_geo),
        'frequency_buckets_json': serialize_for_json(frequency_buckets),
        'customer_trends_json': serialize_for_json(customer_trends),
        'presets': presets,
        'annotations': annotations,
        'db_error': db_error,
    })


@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER])
def revenue_loss_report_view(request):
    role_ctx = _get_role_context(request.user)
    db_error = None
    revenue_data, scrap_data, monthly_rev_loss, category_discounts = [], [], [], []
    total_gross, total_discount, total_net, total_scrapped_qty, total_scrap_loss = 0, 0, 0, 0, 0

    try:
        revenue_data = revenue_loss_service.get_revenue_and_loss_by_year() or []
        scrap_data = revenue_loss_service.get_production_scrap_loss() or []
        monthly_rev_loss = revenue_loss_service.get_monthly_revenue_and_loss() or []
        category_discounts = revenue_loss_service.get_discount_loss_by_category() or []

        total_gross = sum(float(item.get('GrossAmount', 0)) for item in revenue_data)
        total_discount = sum(float(item.get('DiscountLoss', 0)) for item in revenue_data)
        total_net = sum(float(item.get('NetRevenue', 0)) for item in revenue_data)
        total_scrapped_qty = sum(int(item.get('TotalScrappedQty', 0)) for item in scrap_data)
        actual_scrap_sum = sum(float(item.get('ActualScrapCost') or 0) for item in scrap_data)
        total_scrap_loss = int(round(actual_scrap_sum)) if actual_scrap_sum > 0 else (int(total_scrapped_qty * 36.50) if total_scrapped_qty else 0)
    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")

    log_audit_event(
        request.user, 'VIEW', 'Report',
        target_id=request.path,
        module='revenue_loss',
        details="Accessed Revenue & Loss report."
    )
    presets = SavedReportPreset.objects.filter(module='revenue_loss').order_by('-updated_at')
    annotations = ReportAnnotation.objects.filter(module='revenue_loss').order_by('-updated_at')
    data_quality_logs = DataQualityLog.objects.all()
    return render(request, 'reports/revenue_loss.html', {
        **role_ctx,
        'module': 'revenue_loss',
        'revenue_data': revenue_data,
        'revenue_data_json': serialize_for_json(revenue_data),
        'monthly_rev_loss_json': serialize_for_json(monthly_rev_loss),
        'category_discounts_json': serialize_for_json(category_discounts),
        'scrap_data': scrap_data,
        'scrap_data_json': serialize_for_json(scrap_data),
        'total_gross': total_gross,
        'total_discount': total_discount,
        'total_net': total_net,
        'total_scrapped_qty': total_scrapped_qty,
        'total_scrap_loss': total_scrap_loss,
        'data_quality_logs': data_quality_logs,
        'presets': presets,
        'annotations': annotations,
        'db_error': db_error,
    })


@login_required
@role_required([Role.ADMINISTRATOR, Role.MANAGER])
def cost_report_view(request):
    role_ctx = _get_role_context(request.user)
    db_error = None
    margins, vendor_spend, cost_history, category_cost, purchasing_yearly = [], [], [], [], []
    cogs_trend, top_cost_products = [], []

    try:
        margins = cost_service.get_product_margins(50) or []
        vendor_spend = cost_service.get_vendor_purchasing_spend(50) or []
        cost_history = cost_service.get_standard_cost_history(50) or []
        category_cost = cost_service.get_category_cost_summary() or []
        purchasing_yearly = cost_service.get_purchasing_spend_by_year() or []
        cogs_trend = cost_service.get_cogs_trend_by_year_category() or []
        top_cost_products = cost_service.get_top_cost_products(15) or []
    except DatabaseConnectionError as e:
        db_error = str(e)
        messages.error(request, f"Database Error: {e}")

    log_audit_event(
        request.user, 'VIEW', 'Report',
        target_id=request.path,
        module='cost',
        details="Accessed Cost report."
    )
    presets = SavedReportPreset.objects.filter(module='cost').order_by('-updated_at')
    annotations = ReportAnnotation.objects.filter(module='cost').order_by('-updated_at')
    return render(request, 'reports/cost.html', {
        **role_ctx,
        'module': 'cost',
        'margins': margins,
        'margins_json': serialize_for_json(margins),
        'category_cost_json': serialize_for_json(category_cost),
        'vendor_spend': vendor_spend,
        'vendor_spend_json': serialize_for_json(vendor_spend),
        'purchasing_yearly_json': serialize_for_json(purchasing_yearly),
        'cogs_trend_json': serialize_for_json(cogs_trend),
        'top_cost_products_json': serialize_for_json(top_cost_products),
        'cost_history': cost_history,
        'cost_history_json': serialize_for_json(cost_history),
        'presets': presets,
        'annotations': annotations,
        'db_error': db_error,
    })


def _parse_filter_params(post_data, fallback=None):
    raw_json = post_data.get('filter_params_json', '').strip()
    if raw_json:
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, dict) and parsed:
                return parsed
        except (ValueError, TypeError):
            pass
    filter_param = post_data.get('filter_param', '').strip()
    if filter_param:
        return {'filter': filter_param}
    return fallback if fallback is not None else {'filter': 'all'}


@login_required
def save_preset_view(request):
    if request.method == 'POST':
        module = request.POST.get('module', 'sales')
        _require_governance_access(request, module)
        name = request.POST.get('name', '').strip() or 'My Saved Filter'
        filter_params = _parse_filter_params(request.POST)
        preset = SavedReportPreset.objects.create(
            name=name,
            module=module,
            filter_params=filter_params,
            created_by=request.user
        )
        log_audit_event(
            request.user, 'CREATE', 'SavedReportPreset',
            target_id=preset.id, module=module,
            details=f"Created preset '{preset.name}' with filters {json.dumps(filter_params)}."
        )
        messages.success(request, f"Saved preset '{preset.name}' successfully.")
        return redirect(f'report_{module}')
    return redirect('dashboard')


@login_required
def edit_preset_view(request, preset_id):
    preset = get_object_or_404(SavedReportPreset, id=preset_id)
    _require_governance_access(request, preset.module, obj_owner=preset.created_by)
    if request.method == 'POST':
        old_name = preset.name
        new_name = request.POST.get('name', '').strip() or old_name
        preset.name = new_name
        replace_filters = request.POST.get('replace_filters') == '1'
        if replace_filters or 'filter_param' in request.POST:
            preset.filter_params = _parse_filter_params(request.POST, fallback=preset.filter_params)
        preset.save()
        log_audit_event(
            request.user, 'EDIT', 'SavedReportPreset',
            target_id=preset.id, module=preset.module,
            details=f"Updated preset '{old_name}' -> '{preset.name}' (filters: {json.dumps(preset.filter_params)})."
        )
        messages.success(request, f"Updated preset '{preset.name}'.")
    return redirect(f'report_{preset.module}')


@login_required
@require_POST
def delete_preset_view(request, preset_id):
    preset = get_object_or_404(SavedReportPreset, id=preset_id)
    _require_governance_access(request, preset.module, obj_owner=preset.created_by)
    module = preset.module
    name = preset.name
    pid = preset.id
    preset.delete()
    log_audit_event(
        request.user, 'DELETE', 'SavedReportPreset',
        target_id=pid, module=module,
        details=f"Deleted preset '{name}'."
    )
    messages.success(request, f"Preset '{name}' deleted.")
    return redirect(f'report_{module}')


@login_required
def save_annotation_view(request):
    if request.method == 'POST':
        module = request.POST.get('module', 'sales')
        _require_governance_access(request, module)
        title = request.POST.get('title', '').strip() or 'Analytical Note'
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, "Annotation content cannot be empty.")
            return redirect(f'report_{module}')
        note = ReportAnnotation.objects.create(
            module=module,
            title=title,
            content=content,
            author=request.user
        )
        log_audit_event(
            request.user, 'CREATE', 'ReportAnnotation',
            target_id=note.id, module=module,
            details=f"Added note '{note.title}'."
        )
        messages.success(request, f"Added analytical note '{note.title}'.")
        return redirect(f'report_{module}')
    return redirect('dashboard')


@login_required
def edit_annotation_view(request, annotation_id):
    note = get_object_or_404(ReportAnnotation, id=annotation_id)
    _require_governance_access(request, note.module, obj_owner=note.author)
    if request.method == 'POST':
        old_title = note.title
        note.title = request.POST.get('title', '').strip() or old_title
        new_content = request.POST.get('content', '').strip()
        if new_content:
            note.content = new_content
        note.save()
        log_audit_event(
            request.user, 'EDIT', 'ReportAnnotation',
            target_id=note.id, module=note.module,
            details=f"Edited note '{old_title}' -> '{note.title}'."
        )
        messages.success(request, f"Updated note '{note.title}'.")
    return redirect(f'report_{note.module}')


@login_required
@require_POST
def delete_annotation_view(request, annotation_id):
    note = get_object_or_404(ReportAnnotation, id=annotation_id)
    _require_governance_access(request, note.module, obj_owner=note.author)
    module = note.module
    title = note.title
    nid = note.id
    note.delete()
    log_audit_event(
        request.user, 'DELETE', 'ReportAnnotation',
        target_id=nid, module=module,
        details=f"Deleted note '{title}'."
    )
    messages.success(request, f"Note '{title}' deleted.")
    return redirect(f'report_{module}')

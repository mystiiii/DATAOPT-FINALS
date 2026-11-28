from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from accounts import views as account_views
from reports import views as report_views
from governance import views as governance_views

urlpatterns = [
    # Custom in-app User & Role Administration (replaces stock Django Admin UI)
    path('governance/users/', account_views.user_management_view, name='user_management'),
    path('governance/users/create/', account_views.create_user_view, name='create_user'),
    path('governance/users/<int:user_id>/edit/', account_views.edit_user_view, name='edit_user'),
    path('governance/users/<int:user_id>/delete/', account_views.delete_user_view, name='delete_user'),
    path('admin/', RedirectView.as_view(pattern_name='user_management', permanent=False)),
    path('django-admin/', admin.site.urls),

    # Auth & User Settings URLs
    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),
    path('settings/', account_views.settings_view, name='settings'),
    path('preferences/color-scheme/', account_views.update_color_scheme_view, name='update_color_scheme'),

    # Dashboard & Reports
    path('', report_views.dashboard_view, name='dashboard'),
    path('reports/sales/', report_views.sales_report_view, name='report_sales'),
    path('reports/customers/', report_views.customer_report_view, name='report_customers'),
    path('reports/revenue-loss/', report_views.revenue_loss_report_view, name='report_revenue_loss'),
    path('reports/cost/', report_views.cost_report_view, name='report_cost'),

    # Presets & Annotations Governance
    path('presets/save/', report_views.save_preset_view, name='save_preset'),
    path('presets/edit/<int:preset_id>/', report_views.edit_preset_view, name='edit_preset'),
    path('presets/delete/<int:preset_id>/', report_views.delete_preset_view, name='delete_preset'),
    path('annotations/save/', report_views.save_annotation_view, name='save_annotation'),
    path('annotations/edit/<int:annotation_id>/', report_views.edit_annotation_view, name='edit_annotation'),
    path('annotations/delete/<int:annotation_id>/', report_views.delete_annotation_view, name='delete_annotation'),

    # Admin-Only Audit & Governance Log
    path('governance/audit/', governance_views.audit_log_view, name='audit_log'),
]

from django.contrib import admin
from django.urls import path
from accounts import views as account_views
from reports import views as report_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth URLs
    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),
    
    # Dashboard & Reports
    path('', report_views.dashboard_view, name='dashboard'),
    path('reports/sales/', report_views.sales_report_view, name='report_sales'),
    path('reports/customers/', report_views.customer_report_view, name='report_customers'),
    path('reports/revenue-loss/', report_views.revenue_loss_report_view, name='report_revenue_loss'),
    path('reports/cost/', report_views.cost_report_view, name='report_cost'),
    
    # Presets & Governance (View/Edit/Delete application entities)
    path('presets/save/', report_views.save_preset_view, name='save_preset'),
    path('presets/delete/<int:preset_id>/', report_views.delete_preset_view, name='delete_preset'),
]

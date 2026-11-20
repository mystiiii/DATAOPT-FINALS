from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile, Role


SAMPLE_REVENUE = [
    {'Year': 2013, 'OrderCount': 14000, 'GrossAmount': 50000000.0, 'DiscountLoss': 500000.0, 'NetRevenue': 49500000.0},
    {'Year': 2014, 'OrderCount': 10000, 'GrossAmount': 30000000.0, 'DiscountLoss': 200000.0, 'NetRevenue': 29800000.0},
]
SAMPLE_CAT_YEAR = [
    {'Category': 'Bikes', 'Year': 2013, 'Revenue': 45000000.0, 'UnitsSold': 30000, 'ManufacturingCost': 28000000.0, 'GrossProfit': 17000000.0},
    {'Category': 'Bikes', 'Year': 2014, 'Revenue': 27000000.0, 'UnitsSold': 18000, 'ManufacturingCost': 17000000.0, 'GrossProfit': 10000000.0},
]
SAMPLE_TERRITORIES = [
    {'TerritoryName': 'Southwest', 'TerritoryGroup': 'North America', 'TotalOrders': 6224, 'TotalRevenue': 27150594.0},
    {'TerritoryName': 'Germany', 'TerritoryGroup': 'Europe', 'TotalOrders': 2623, 'TotalRevenue': 5479819.0},
]
SAMPLE_CUST_TYPES = [
    {'CustomerType': 'Store / B2B', 'TotalCustomers': 635, 'TotalOrders': 3806, 'TotalRevenue': 90775447.0},
    {'CustomerType': 'Individual / B2C', 'TotalCustomers': 18484, 'TotalOrders': 27659, 'TotalRevenue': 32441339.0},
]
SAMPLE_TOP_PRODUCTS = [
    {'ProductID': 782, 'ProductName': 'Mountain-200 Black, 38', 'Category': 'Bikes', 'TotalRevenue': 4400592.0, 'TotalQuantity': 2977, 'TotalCost': 2500000.0, 'MarginPercentage': 43.2},
]
SAMPLE_TOP_CUSTOMERS = [
    {'CustomerID': 29818, 'CustomerName': 'Brakes and Gears', 'CustomerType': 'Store (B2B)', 'Orders': 12, 'TotalSpent': 989184.0},
]
SAMPLE_SCRAP = [
    {'ScrapReason': 'Paint process failed', 'ScrapOrders': 150, 'TotalScrappedQty': 1271},
]
SAMPLE_VENDORS = [
    {'VendorID': 1496, 'VendorName': 'Superior Bicycles', 'PurchaseOrdersCount': 45, 'TotalSpent': 5034267.0},
]


class DashboardAndLayoutTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='boss', password='pw')
        UserProfile.objects.create(user=self.admin, role=Role.ADMINISTRATOR)

        self.emp = User.objects.create_user(username='staff', password='pw')
        UserProfile.objects.create(user=self.emp, role=Role.EMPLOYEE)

    @patch('reports.views.cost_service.get_vendor_purchasing_spend', return_value=SAMPLE_VENDORS)
    @patch('reports.views.customer_service.get_top_customers', return_value=SAMPLE_TOP_CUSTOMERS)
    @patch('reports.views.sales_service.get_top_selling_products', return_value=SAMPLE_TOP_PRODUCTS)
    @patch('reports.views.sales_service.get_territory_sales', return_value=SAMPLE_TERRITORIES)
    @patch('reports.views.sales_service.get_sales_by_category_and_year', return_value=SAMPLE_CAT_YEAR)
    @patch('reports.views.revenue_loss_service.get_revenue_and_loss_by_year', return_value=SAMPLE_REVENUE)
    @patch('reports.views.customer_service.get_customer_type_breakdown', return_value=SAMPLE_CUST_TYPES)
    @patch('reports.views.revenue_loss_service.get_production_scrap_loss', return_value=SAMPLE_SCRAP)
    def test_admin_dashboard_full_width_and_charts(self, *_):
        self.client.login(username='boss', password='pw')
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()

        # 3rd column removed
        self.assertNotIn('lg:w-72 xl:w-80', html)
        # Charts and explorer present
        self.assertIn('categoryChart', html)
        self.assertIn('waterfallChart', html)
        self.assertIn('territoryRankChart', html)
        self.assertIn('customerSplitChart', html)
        self.assertIn('Factory Scrap', html)
        self.assertIn('Suppliers', html)
        # Accurate profit & discount calculation in context
        self.assertEqual(resp.context['total_discount'], 700000.0)
        self.assertEqual(resp.context['total_scrap_loss'], int(1271 * 36.50))
        self.assertEqual(resp.context['total_real_profit'], 79300000.0 - 45000000.0 - int(1271 * 36.50))

    @patch('reports.views.cost_service.get_vendor_purchasing_spend', return_value=SAMPLE_VENDORS)
    @patch('reports.views.customer_service.get_top_customers', return_value=SAMPLE_TOP_CUSTOMERS)
    @patch('reports.views.sales_service.get_top_selling_products', return_value=SAMPLE_TOP_PRODUCTS)
    @patch('reports.views.sales_service.get_territory_sales', return_value=SAMPLE_TERRITORIES)
    @patch('reports.views.sales_service.get_sales_by_category_and_year', return_value=SAMPLE_CAT_YEAR)
    @patch('reports.views.revenue_loss_service.get_revenue_and_loss_by_year', return_value=SAMPLE_REVENUE)
    @patch('reports.views.customer_service.get_customer_type_breakdown', return_value=SAMPLE_CUST_TYPES)
    @patch('reports.views.revenue_loss_service.get_production_scrap_loss', return_value=SAMPLE_SCRAP)
    def test_employee_rbac_hides_scrap_and_vendor_tabs(self, *_):
        self.client.login(username='staff', password='pw')
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()

        self.assertNotIn('Factory Scrap', html)
        self.assertNotIn('Suppliers', html)
        self.assertEqual(resp.context['scrap_list_json'], '[]')
        self.assertEqual(resp.context['vendor_list_json'], '[]')

    @patch('reports.views.sales_service.get_territory_sales', return_value=SAMPLE_TERRITORIES)
    @patch('reports.views.sales_service.get_top_selling_products', return_value=SAMPLE_TOP_PRODUCTS)
    @patch('reports.views.sales_service.get_sales_by_category_and_year', return_value=SAMPLE_CAT_YEAR)
    @patch('reports.views.customer_service.get_customer_geographic_distribution', return_value=[])
    @patch('reports.views.customer_service.get_customer_type_breakdown', return_value=SAMPLE_CUST_TYPES)
    @patch('reports.views.customer_service.get_top_customers', return_value=SAMPLE_TOP_CUSTOMERS)
    @patch('reports.views.revenue_loss_service.get_production_scrap_loss', return_value=SAMPLE_SCRAP)
    @patch('reports.views.revenue_loss_service.get_revenue_and_loss_by_year', return_value=SAMPLE_REVENUE)
    @patch('reports.views.cost_service.get_standard_cost_history', return_value=[])
    @patch('reports.views.cost_service.get_vendor_purchasing_spend', return_value=SAMPLE_VENDORS)
    @patch('reports.views.cost_service.get_product_margins', return_value=[])
    def test_all_module_pages_render_without_third_column(self, *_):
        self.client.login(username='boss', password='pw')
        for url_name in ['report_sales', 'report_customers', 'report_revenue_loss', 'report_cost']:
            resp = self.client.get(reverse(url_name))
            self.assertEqual(resp.status_code, 200, msg=f"Failed on {url_name}")
            self.assertNotIn('lg:w-72 xl:w-80', resp.content.decode())

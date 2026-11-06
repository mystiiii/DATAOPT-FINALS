from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from accounts.models import UserProfile, Role
from governance.models import SavedReportPreset

class RBACTestCase(TestCase):
    databases = {'default', 'adventureworks'}

    def setUp(self):
        self.client = Client()

        # Create Roles
        self.admin_user = User.objects.create_user(username='admin', password='Password123!')
        UserProfile.objects.create(user=self.admin_user, role=Role.ADMINISTRATOR)

        self.manager_user = User.objects.create_user(username='manager', password='Password123!')
        UserProfile.objects.create(user=self.manager_user, role=Role.MANAGER)

        self.supervisor_user = User.objects.create_user(username='supervisor', password='Password123!')
        UserProfile.objects.create(user=self.supervisor_user, role=Role.SUPERVISOR)

        self.employee_user = User.objects.create_user(username='employee', password='Password123!')
        UserProfile.objects.create(user=self.employee_user, role=Role.EMPLOYEE)

    def test_unauthenticated_redirect(self):
        """Unauthenticated requests across all protected routes must redirect to login."""
        protected_routes = ['dashboard', 'report_sales', 'report_customers', 'report_revenue_loss', 'report_cost']
        for route in protected_routes:
            response = self.client.get(reverse(route))
            self.assertEqual(response.status_code, 302, f"Route '{route}' did not redirect anonymous user.")
            self.assertIn(reverse('login'), response.url)

    def test_employee_access_limits(self):
        """Employee can access Sales and Customers, but is denied on Revenue/Loss and Cost."""
        self.client.login(username='employee', password='Password123!')

        # Permitted
        res_sales = self.client.get(reverse('report_sales'))
        self.assertEqual(res_sales.status_code, 200)

        res_cust = self.client.get(reverse('report_customers'))
        self.assertEqual(res_cust.status_code, 200)

        # Forbidden (403 PermissionDenied)
        res_rev = self.client.get(reverse('report_revenue_loss'))
        self.assertEqual(res_rev.status_code, 403)

        res_cost = self.client.get(reverse('report_cost'))
        self.assertEqual(res_cost.status_code, 403)

    def test_manager_full_access(self):
        """Manager has access to all 4 reporting modules."""
        self.client.login(username='manager', password='Password123!')

        for route in ['report_sales', 'report_customers', 'report_revenue_loss', 'report_cost']:
            res = self.client.get(reverse(route))
            self.assertEqual(res.status_code, 200)

    def test_preset_creation_and_permissions(self):
        """Test preset creation and ownership deletion permissions."""
        self.client.login(username='employee', password='Password123!')

        # Create preset
        self.client.post(reverse('save_preset'), {
            'module': 'sales',
            'name': 'Employee Filter',
            'filter_param': 'bikes_only'
        })
        preset = SavedReportPreset.objects.get(name='Employee Filter')
        self.assertEqual(preset.created_by, self.employee_user)

        # Supervisor cannot delete Employee's preset
        self.client.login(username='supervisor', password='Password123!')
        res_delete_sup = self.client.get(reverse('delete_preset', args=[preset.id]))
        self.assertTrue(SavedReportPreset.objects.filter(id=preset.id).exists())

        # Manager can delete any preset
        self.client.login(username='manager', password='Password123!')
        res_delete_mgr = self.client.get(reverse('delete_preset', args=[preset.id]))
        self.assertFalse(SavedReportPreset.objects.filter(id=preset.id).exists())

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import UserProfile, Role
from governance.models import SavedReportPreset, ReportAnnotation, AuditLog


class RBACTestCase(TestCase):
    databases = {'default', 'adventureworks'}

    def setUp(self):
        self.client = Client()

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
        protected_routes = ['dashboard', 'report_sales', 'report_customers', 'report_revenue_loss', 'report_cost', 'audit_log']
        for route in protected_routes:
            response = self.client.get(reverse(route))
            self.assertEqual(response.status_code, 302, f"Route '{route}' did not redirect anonymous user.")
            self.assertIn(reverse('login'), response.url)

    def test_employee_access_limits(self):
        """Employee can access Sales only; Customers, Revenue/Loss, Cost, and Audit Log return 403 and log ACCESS_DENIED."""
        self.client.login(username='employee', password='Password123!')

        self.assertEqual(self.client.get(reverse('report_sales')).status_code, 200)
        self.assertEqual(self.client.get(reverse('report_customers')).status_code, 403)
        self.assertEqual(self.client.get(reverse('report_revenue_loss')).status_code, 403)
        self.assertEqual(self.client.get(reverse('report_cost')).status_code, 403)
        self.assertEqual(self.client.get(reverse('audit_log')).status_code, 403)
        self.assertEqual(AuditLog.objects.filter(action='ACCESS_DENIED', username_snapshot='employee').count(), 4)

    def test_supervisor_access_limits(self):
        """Supervisor can access Sales and Customers, but is denied Revenue/Loss, Cost, and Audit Log."""
        self.client.login(username='supervisor', password='Password123!')
        self.assertEqual(self.client.get(reverse('report_sales')).status_code, 200)
        self.assertEqual(self.client.get(reverse('report_customers')).status_code, 200)
        self.assertEqual(self.client.get(reverse('report_revenue_loss')).status_code, 403)
        self.assertEqual(self.client.get(reverse('report_cost')).status_code, 403)
        self.assertEqual(self.client.get(reverse('audit_log')).status_code, 403)

    def test_manager_and_admin_access(self):
        """Manager accesses all 4 reports but not Admin Audit Log; Administrator accesses Audit Log too."""
        self.client.login(username='manager', password='Password123!')
        for route in ['report_sales', 'report_customers', 'report_revenue_loss', 'report_cost']:
            self.assertEqual(self.client.get(reverse(route)).status_code, 200)
        self.assertEqual(self.client.get(reverse('audit_log')).status_code, 403)

        self.client.login(username='admin', password='Password123!')
        self.assertEqual(self.client.get(reverse('audit_log')).status_code, 200)

    def test_governance_view_edit_delete_and_audit_log(self):
        """Employee is view-only; Supervisor can create/edit/delete own in sales/customers; Manager can edit/delete any."""
        # Employee blocked from creating preset or annotation
        self.client.login(username='employee', password='Password123!')
        res_emp_post = self.client.post(reverse('save_preset'), {'module': 'sales', 'name': 'Emp Preset', 'filter_param': '2013'})
        self.assertEqual(res_emp_post.status_code, 403)
        self.assertFalse(SavedReportPreset.objects.filter(name='Emp Preset').exists())

        # Supervisor creates preset + annotation in sales, but blocked from cost
        self.client.login(username='supervisor', password='Password123!')
        self.assertEqual(
            self.client.post(reverse('save_preset'), {'module': 'cost', 'name': 'Cost Hack', 'filter_param': 'all'}).status_code,
            403
        )
        self.client.post(reverse('save_preset'), {'module': 'sales', 'name': 'Sup Filter', 'filter_param': '2013'})
        preset = SavedReportPreset.objects.get(name='Sup Filter')
        self.assertEqual(preset.created_by, self.supervisor_user)

        self.client.post(reverse('edit_preset', args=[preset.id]), {'name': 'Sup Filter v2', 'filter_param': '2014'})
        preset.refresh_from_db()
        self.assertEqual(preset.name, 'Sup Filter v2')

        self.client.post(reverse('save_annotation'), {'module': 'sales', 'title': 'Q4 Spike', 'content': 'Strong holiday sales.'})
        note = ReportAnnotation.objects.get(title='Q4 Spike')

        # Manager can edit/delete Supervisor's preset & annotation
        self.client.login(username='manager', password='Password123!')
        self.client.post(reverse('edit_annotation', args=[note.id]), {'title': 'Q4 Spike Reviewed', 'content': 'Verified.'})
        note.refresh_from_db()
        self.assertEqual(note.title, 'Q4 Spike Reviewed')

        self.client.get(reverse('delete_preset', args=[preset.id]))
        self.assertFalse(SavedReportPreset.objects.filter(id=preset.id).exists())

        self.client.get(reverse('delete_annotation', args=[note.id]))
        self.assertFalse(ReportAnnotation.objects.filter(id=note.id).exists())

        self.assertTrue(AuditLog.objects.filter(action='CREATE', target_type='SavedReportPreset').exists())
        self.assertTrue(AuditLog.objects.filter(action='EDIT', target_type='ReportAnnotation').exists())
        self.assertTrue(AuditLog.objects.filter(action='DELETE', target_type='SavedReportPreset').exists())

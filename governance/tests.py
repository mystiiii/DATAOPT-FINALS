from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import UserProfile, Role
from governance.models import AuditLog, DataQualityLog, log_audit_event


class GovernanceAndAuthSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='gov_admin', password='Password123!')
        UserProfile.objects.create(user=self.admin, role=Role.ADMINISTRATOR)

    def test_audit_log_filters_and_data_quality(self):
        DataQualityLog.objects.create(
            issue_title='Test limit',
            affected_tables='Sales.Customer',
            evidence_query='SELECT 1;',
            impact_description='Impact',
            handling_strategy='Strategy',
            severity='INFO',
        )
        log_audit_event(self.admin, 'CREATE', 'SavedReportPreset', target_id='1', module='sales', details='Created test preset')
        self.client.login(username='gov_admin', password='Password123!')
        resp = self.client.get(reverse('audit_log'), {'action': 'CREATE', 'module': 'sales', 'q': 'test'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Created test preset')
        self.assertNotContains(resp, 'Known data limits')
        self.assertNotContains(resp, 'Logged events')

    def test_login_blocks_external_next_redirect(self):
        resp = self.client.post(reverse('login'), {
            'username': 'gov_admin',
            'password': 'Password123!',
            'next': 'https://evil.example.com/phish',
        })
        self.assertRedirects(resp, reverse('dashboard'), fetch_redirect_response=False)

    def test_login_allows_local_next_redirect(self):
        resp = self.client.post(reverse('login'), {
            'username': 'gov_admin',
            'password': 'Password123!',
            'next': reverse('audit_log'),
        })
        self.assertRedirects(resp, reverse('audit_log'), fetch_redirect_response=False)

    def test_user_activity_logs_views_login_and_logout(self):
        self.client.post(reverse('login'), {'username': 'gov_admin', 'password': 'Password123!'})
        self.assertTrue(AuditLog.objects.filter(action='LOGIN', username_snapshot='gov_admin').exists())

        self.client.get(reverse('dashboard'))
        self.assertTrue(AuditLog.objects.filter(action='VIEW', module='dashboard', username_snapshot='gov_admin').exists())

        self.client.get(reverse('report_sales'))
        self.assertTrue(AuditLog.objects.filter(action='VIEW', module='sales', username_snapshot='gov_admin').exists())

        self.client.get(reverse('logout'))
        self.assertTrue(AuditLog.objects.filter(action='LOGOUT', username_snapshot='gov_admin').exists())

    def test_audit_log_role_scoping(self):
        mgr = User.objects.create_user(username='gov_mgr', password='Password123!')
        UserProfile.objects.create(user=mgr, role=Role.MANAGER)
        sup = User.objects.create_user(username='gov_sup', password='Password123!')
        UserProfile.objects.create(user=sup, role=Role.SUPERVISOR)
        emp = User.objects.create_user(username='gov_emp', password='Password123!')
        UserProfile.objects.create(user=emp, role=Role.EMPLOYEE)

        log_audit_event(self.admin, 'CREATE', 'User', module='auth', details='Admin event secret')
        log_audit_event(mgr, 'CREATE', 'SavedReportPreset', module='cost', details='Manager event visible')
        log_audit_event(sup, 'EDIT', 'SavedReportPreset', module='sales', details='Supervisor event visible')
        log_audit_event(emp, 'ACCESS_DENIED', 'Route', module='cost', details='Employee event visible')

        # Admin sees all 4 roles
        self.client.login(username='gov_admin', password='Password123!')
        admin_resp = self.client.get(reverse('audit_log'))
        self.assertContains(admin_resp, 'Admin event secret')
        self.assertContains(admin_resp, 'Manager event visible')
        self.assertContains(admin_resp, 'Supervisor event visible')
        self.assertContains(admin_resp, 'Employee event visible')

        # Manager sees Manager, Supervisor, Employee — NOT Admin
        self.client.login(username='gov_mgr', password='Password123!')
        mgr_resp = self.client.get(reverse('audit_log'))
        self.assertEqual(mgr_resp.status_code, 200)
        self.assertNotContains(mgr_resp, 'Admin event secret')
        self.assertContains(mgr_resp, 'Manager event visible')
        self.assertContains(mgr_resp, 'Supervisor event visible')
        self.assertContains(mgr_resp, 'Employee event visible')
        self.assertNotContains(mgr_resp, 'Manage Users &amp; Roles')

        # Supervisor sees Supervisor, Employee — NOT Admin or Manager
        self.client.login(username='gov_sup', password='Password123!')
        sup_resp = self.client.get(reverse('audit_log'))
        self.assertEqual(sup_resp.status_code, 200)
        self.assertNotContains(sup_resp, 'Admin event secret')
        self.assertNotContains(sup_resp, 'Manager event visible')
        self.assertContains(sup_resp, 'Supervisor event visible')
        self.assertContains(sup_resp, 'Employee event visible')
        self.assertNotContains(sup_resp, 'Manage Users &amp; Roles')

        # Employee is denied (403)
        self.client.login(username='gov_emp', password='Password123!')
        self.assertEqual(self.client.get(reverse('audit_log')).status_code, 403)

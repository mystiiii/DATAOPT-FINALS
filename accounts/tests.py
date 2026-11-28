from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry
from django.urls import reverse
from accounts.models import UserProfile, Role, ColorScheme
from governance.models import SavedReportPreset, ReportAnnotation, AuditLog


class RBACTestCase(TestCase):
    databases = {'default'}

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
        self.client.post(reverse('save_preset'), {
            'module': 'sales',
            'name': 'Sup Filter',
            'filter_params_json': '{"year": "2013", "category": "Clothing", "region": "all"}'
        })
        preset = SavedReportPreset.objects.get(name='Sup Filter')
        self.assertEqual(preset.created_by, self.supervisor_user)
        self.assertEqual(preset.filter_params, {'year': '2013', 'category': 'Clothing', 'region': 'all'})

        # Verify preset JSON script tag renders with its numeric ID so Apply button can find it
        res_sales = self.client.get(reverse('report_sales'))
        self.assertIn(f'id="preset-data-{preset.id}"', res_sales.content.decode())

        self.client.post(reverse('edit_preset', args=[preset.id]), {
            'name': 'Sup Filter v2',
            'replace_filters': '1',
            'filter_params_json': '{"year": "2014", "category": "Bikes"}'
        })
        preset.refresh_from_db()
        self.assertEqual(preset.name, 'Sup Filter v2')
        self.assertEqual(preset.filter_params, {'year': '2014', 'category': 'Bikes'})

        self.client.post(reverse('save_annotation'), {'module': 'sales', 'title': 'Q4 Spike', 'content': 'Strong holiday sales.'})
        note = ReportAnnotation.objects.get(title='Q4 Spike')

        # Manager can edit/delete Supervisor's preset & annotation
        self.client.login(username='manager', password='Password123!')
        self.client.post(reverse('edit_annotation', args=[note.id]), {'title': 'Q4 Spike Reviewed', 'content': 'Verified.'})
        note.refresh_from_db()
        self.assertEqual(note.title, 'Q4 Spike Reviewed')

        # GET delete should be rejected (405 Method Not Allowed)
        self.assertEqual(self.client.get(reverse('delete_preset', args=[preset.id])).status_code, 405)
        self.assertTrue(SavedReportPreset.objects.filter(id=preset.id).exists())

        self.client.post(reverse('delete_preset', args=[preset.id]))
        self.assertFalse(SavedReportPreset.objects.filter(id=preset.id).exists())

        self.assertEqual(self.client.get(reverse('delete_annotation', args=[note.id])).status_code, 405)
        self.client.post(reverse('delete_annotation', args=[note.id]))
        self.assertFalse(ReportAnnotation.objects.filter(id=note.id).exists())

        self.assertTrue(AuditLog.objects.filter(action='CREATE', target_type='SavedReportPreset').exists())
        self.assertTrue(AuditLog.objects.filter(action='EDIT', target_type='ReportAnnotation').exists())
        self.assertTrue(AuditLog.objects.filter(action='DELETE', target_type='SavedReportPreset').exists())

    def test_custom_user_management_admin_ui_and_django_admin_system(self):
        """Only Administrators can access custom Users & Roles UI; CRUD syncs Django User, Group, UserProfile, and admin LogEntry."""
        # Non-admins are denied
        for uname in ['employee', 'supervisor', 'manager']:
            self.client.login(username=uname, password='Password123!')
            self.assertEqual(self.client.get(reverse('user_management')).status_code, 403)
            self.assertEqual(self.client.post(reverse('create_user'), {'username': 'x', 'password': 'pw'}).status_code, 403)

        # Administrator accesses custom Users & Roles page (and /admin/ redirects to it)
        self.client.login(username='admin', password='Password123!')
        res_redirect = self.client.get('/admin/')
        self.assertEqual(res_redirect.status_code, 302)
        self.assertEqual(res_redirect.url, reverse('user_management'))

        res_page = self.client.get(reverse('user_management'))
        self.assertEqual(res_page.status_code, 200)
        self.assertIn('Users &amp; roles administration', res_page.content.decode())

        # Create a new Supervisor user via custom UI
        self.client.post(reverse('create_user'), {
            'username': 'new_sup',
            'password': 'NewPassword123!',
            'email': 'new_sup@adventureworks.com',
            'first_name': 'New',
            'last_name': 'Supervisor',
            'role': Role.SUPERVISOR,
            'department': 'Regional Sales',
            'is_active': '1',
        })
        created_u = User.objects.get(username='new_sup')
        self.assertEqual(created_u.profile.role, Role.SUPERVISOR)
        self.assertEqual(created_u.profile.department, 'Regional Sales')
        self.assertTrue(created_u.groups.filter(name=Role.SUPERVISOR).exists())
        self.assertTrue(LogEntry.objects.filter(object_repr='new_sup').exists())

        # Edit user role to Manager and reset password
        self.client.post(reverse('edit_user', args=[created_u.pk]), {
            'username': 'new_sup',
            'email': 'promoted@adventureworks.com',
            'first_name': 'Promoted',
            'last_name': 'Manager',
            'role': Role.MANAGER,
            'department': 'Executive Finance',
            'password': 'UpdatedPassword123!',
            'is_active': '1',
        })
        created_u.refresh_from_db()
        created_u.profile.refresh_from_db()
        self.assertEqual(created_u.profile.role, Role.MANAGER)
        self.assertEqual(created_u.email, 'promoted@adventureworks.com')
        self.assertTrue(created_u.groups.filter(name=Role.MANAGER).exists())
        self.assertTrue(created_u.check_password('UpdatedPassword123!'))

        # Admin cannot delete or demote themselves
        self.client.post(reverse('delete_user', args=[self.admin_user.pk]))
        self.assertTrue(User.objects.filter(pk=self.admin_user.pk).exists())

        # Delete created user
        self.client.post(reverse('delete_user', args=[created_u.pk]))
        self.assertFalse(User.objects.filter(pk=created_u.pk).exists())

    def test_color_scheme_selection_available_to_all_roles(self):
        """All user roles (Employee, Supervisor, Manager, Administrator) can access Settings and pick preset or custom colors."""
        # Anonymous users are redirected to login
        self.assertEqual(self.client.get(reverse('settings')).status_code, 302)
        anon_res = self.client.post(reverse('update_color_scheme'), {'scheme': ColorScheme.CALM_TEAL})
        self.assertEqual(anon_res.status_code, 302)
        self.assertIn(reverse('login'), anon_res.url)

        # Every role can open /settings/ and save a preset or custom palette independently
        role_presets = [
            ('employee', ColorScheme.CALM_TEAL),
            ('supervisor', ColorScheme.FOREST_SAGE),
            ('manager', ColorScheme.ROYAL_PLUM),
            ('admin', ColorScheme.WARM_SAND),
        ]
        for uname, scheme in role_presets:
            self.client.login(username=uname, password='Password123!')
            page = self.client.get(reverse('settings'))
            self.assertEqual(page.status_code, 200, f"Role '{uname}' could not access Settings tab.")
            self.assertIn('Choose your own interface and chart colors', page.content.decode())

            res = self.client.post(reverse('settings'), {
                'action': 'save',
                'color_scheme': scheme,
            })
            self.assertEqual(res.status_code, 302)
            user_obj = User.objects.get(username=uname)
            self.assertEqual(user_obj.profile.color_scheme, scheme)

        # Employee saves fully custom hex colors via Settings form
        self.client.login(username='employee', password='Password123!')
        custom_post = self.client.post(reverse('settings'), {
            'action': 'save',
            'color_scheme': ColorScheme.CUSTOM,
            'color_accent': '#1A6B8A',
            'color_canvas': '#F2F6F8',
            'color_card': '#FFFFFF',
            'color_text': '#1C2E3A',
            'color_primary': '#2E86AB',
            'color_anchor': '#51718A',
            'color_positive': '#389E82',
            'color_secondary': '#6B74C4',
            'color_warning': '#8B68B0',
            'color_negative': '#C45B72',
        })
        self.assertEqual(custom_post.status_code, 302)
        self.employee_user.profile.refresh_from_db()
        self.assertEqual(self.employee_user.profile.color_scheme, ColorScheme.CUSTOM)
        self.assertEqual(self.employee_user.profile.custom_colors['accent'], '#1A6B8A')
        self.assertEqual(self.employee_user.profile.custom_colors['primary'], '#2E86AB')

        # Rendered Settings page includes data-theme="custom" and serialized custom colors JSON
        settings_html = self.client.get(reverse('settings')).content.decode()
        self.assertIn('data-theme="custom"', settings_html)
        self.assertIn('#1A6B8A', settings_html)

        # Reset returns Employee to default Classic Slate
        reset_res = self.client.post(reverse('settings'), {'action': 'reset'})
        self.assertEqual(reset_res.status_code, 302)
        self.employee_user.profile.refresh_from_db()
        self.assertEqual(self.employee_user.profile.color_scheme, ColorScheme.SLATE_BLUE)
        self.assertEqual(self.employee_user.profile.custom_colors, {})

        # Invalid color scheme via JSON endpoint returns HTTP 400
        bad_res = self.client.post(
            reverse('update_color_scheme'),
            data='{"scheme": "invalid-theme"}',
            content_type='application/json',
        )
        self.assertEqual(bad_res.status_code, 400)

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from accounts.models import UserProfile, Role
from governance.models import DataQualityLog

class Command(BaseCommand):
    help = 'Seeds initial RBAC groups, default demo user accounts, and data quality logs'

    def handle(self, *args, **options):
        self.stdout.write("Setting up RBAC Roles and Groups...")

        roles = [
            Role.ADMINISTRATOR,
            Role.MANAGER,
            Role.SUPERVISOR,
            Role.EMPLOYEE,
        ]

        for role_name in roles:
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(f"  Created Group: {role_name}")

        demo_users = [
            ('admin', 'admin@adventureworks.com', 'Admin123!', Role.ADMINISTRATOR, 'Executive / IT'),
            ('manager', 'manager@adventureworks.com', 'Manager123!', Role.MANAGER, 'Sales & Finance'),
            ('supervisor', 'supervisor@adventureworks.com', 'Supervisor123!', Role.SUPERVISOR, 'Regional Operations'),
            ('employee', 'employee@adventureworks.com', 'Employee123!', Role.EMPLOYEE, 'Sales Team'),
        ]

        for username, email, password, role, dept in demo_users:
            user, created = User.objects.get_or_create(username=username, defaults={'email': email})
            user.set_password(password)
            if role == Role.ADMINISTRATOR:
                user.is_staff = True
                user.is_superuser = True
            user.save()

            group = Group.objects.get(name=role)
            user.groups.clear()
            user.groups.add(group)

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.department = dept
            profile.save()

            status = "Created" if created else "Updated"
            self.stdout.write(f"  {status} User: {username} ({role}) - Pass: {password}")

        self.stdout.write("\nSeeding initial data quality logs...")
        quality_issues = [
            {
                'issue_title': 'No returns or refunds table',
                'affected_tables': 'Sales.SalesOrderHeader, Sales.SalesOrderDetail',
                'evidence_query': "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Return%'; -- Returns 0 rows",
                'impact_description': 'AdventureWorks does not track customer returns or refunds.',
                'handling_strategy': 'Loss is estimated using discounts (UnitPriceDiscount) and scrapped work orders (WorkOrder.ScrappedQty).',
                'severity': 'HIGH'
            },
            {
                'issue_title': 'Customer records split across person and store tables',
                'affected_tables': 'Sales.Customer, Person.Person, Sales.Store',
                'evidence_query': "SELECT COUNT(*) FROM Sales.Customer WHERE PersonID IS NULL AND StoreID IS NOT NULL;",
                'impact_description': 'Inner joins drop either store accounts or individual buyers.',
                'handling_strategy': "Use LEFT JOIN with COALESCE(CONCAT(p.FirstName, ' ', p.LastName), s.Name) to include both types.",
                'severity': 'MEDIUM'
            },
            {
                'issue_title': 'Orders end in June 2014',
                'affected_tables': 'Sales.SalesOrderHeader',
                'evidence_query': "SELECT MIN(OrderDate) AS Earliest, MAX(OrderDate) AS Latest FROM Sales.SalesOrderHeader;",
                'impact_description': 'Orders end mid-year, so year-over-year comparisons need to compare matching months rather than full calendar years.',
                'handling_strategy': 'Label 2014 as a partial year and compare matching monthly windows.',
                'severity': 'INFO'
            }
        ]

        for issue in quality_issues:
            obj, created = DataQualityLog.objects.get_or_create(
                issue_title=issue['issue_title'],
                defaults=issue
            )
            if created:
                self.stdout.write(f"  Logged quality issue: {issue['issue_title']}")

        self.stdout.write(self.style.SUCCESS("\nRBAC setup and data logs seeded successfully."))

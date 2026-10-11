from django.test import TestCase

# Create your tests here.

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


class DashboardPermissionTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.url = reverse("farm_overview")

        admin_group, _ = Group.objects.get_or_create(
            name="Administrator"
        )

        staff_group, _ = Group.objects.get_or_create(
            name="Farm Staff"
        )

        self.admin_user = User.objects.create_user(
            username="dashboard_admin",
            password="TestPassword123!"
        )

        self.staff_user = User.objects.create_user(
            username="dashboard_staff",
            password="TestPassword123!"
        )

        self.admin_user.groups.add(admin_group)
        self.staff_user.groups.add(staff_group)

    def test_administrator_dashboard(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Administrator Dashboard"
        )
        self.assertIn(
            "total_revenue",
            response.context
        )

    def test_farm_staff_dashboard(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Farm Staff Dashboard"
        )

        self.assertNotIn(
            "total_revenue",
            response.context
        )

        self.assertNotIn(
            "total_expenses",
            response.context
        )

        self.assertNotIn(
            "net_income",
            response.context
        )

        self.assertNotContains(
            response,
            "Financial Overview"
        )

        self.assertNotContains(
            response,
            "View Detailed Accounting Reports"
        )

    def test_unauthenticated_user_redirected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

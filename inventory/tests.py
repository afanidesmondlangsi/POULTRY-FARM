from django.test import TestCase

# Create your tests here.

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


class FeedInventoryPermissionTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.url = reverse("feed_dashboard")

        self.admin_user = User.objects.create_user(
            username="inventory_admin",
            password="TestPassword123!"
        )

        self.staff_user = User.objects.create_user(
            username="inventory_staff",
            password="TestPassword123!"
        )

        self.other_user = User.objects.create_user(
            username="inventory_other",
            password="TestPassword123!"
        )

        admin_group, _ = Group.objects.get_or_create(
            name="Administrator"
        )

        staff_group, _ = Group.objects.get_or_create(
            name="Farm Staff"
        )

        self.admin_user.groups.add(admin_group)
        self.staff_user.groups.add(staff_group)

    def test_administrator_can_view_inventory(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_farm_staff_can_view_inventory(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_unassigned_user_cannot_view_inventory(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

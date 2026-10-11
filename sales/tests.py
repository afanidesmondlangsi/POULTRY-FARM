from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from inventory.models import EggStockMovement
from sales.models import Sale, SaleCorrection
from sales.services import record_sale, correct_sale


class SalesTransactionTests(TestCase):

    def setUp(self):
        # Create a temporary test user
        self.user = get_user_model().objects.create_user(
            username="sales_test_user",
            password="TestPassword123!"
        )

        # Create 1,500 eggs in the test database
        EggStockMovement.objects.create(
            movement_type="HARVEST",
            eggs=1500,
            reference="TEST-HARVEST"
        )

    def test_sale_deducts_inventory(self):
        sale = record_sale(
            recorded_by=self.user,
            product_type="FULL_TRAY",
            quantity=5,
            unit_price=Decimal("10.00")
        )

        self.assertEqual(sale.eggs_sold, 150)
        self.assertEqual(sale.total_amount, Decimal("50.00"))
        self.assertEqual(EggStockMovement.current_stock(), 1350)

        self.assertEqual(Sale.objects.count(), 1)

        self.assertTrue(
            EggStockMovement.objects.filter(
                movement_type="SALE",
                reference=f"SALE-{sale.id}",
                eggs=-150
            ).exists()
        )

    def test_insufficient_inventory(self):
        with self.assertRaises(ValidationError):
            record_sale(
                recorded_by=self.user,
                product_type="FULL_TRAY",
                quantity=60,
                unit_price=Decimal("10.00")
            )

        # Failed sale must not change inventory
        self.assertEqual(EggStockMovement.current_stock(), 1500)
        self.assertEqual(Sale.objects.count(), 0)

    def test_half_tray_sale(self):
        sale = record_sale(
            recorded_by=self.user,
            product_type="HALF_TRAY",
            quantity=4,
            unit_price=Decimal("5.00")
        )

        self.assertEqual(sale.eggs_sold, 60)
        self.assertEqual(sale.total_amount, Decimal("20.00"))
        self.assertEqual(EggStockMovement.current_stock(), 1440)

    def test_box_sale(self):
        sale = record_sale(
            recorded_by=self.user,
            product_type="BOX",
            quantity=2,
            trays_per_box=12,
            unit_price=Decimal("100.00")
        )

        self.assertEqual(sale.eggs_sold, 720)
        self.assertEqual(sale.total_amount, Decimal("200.00"))
        self.assertEqual(EggStockMovement.current_stock(), 780)

from django.contrib.auth.models import Group
from django.urls import reverse


class SalesDashboardPermissionTests(TestCase):

    def setUp(self):

        User = get_user_model()

        self.url = reverse("sales_dashboard")

        admin_group, _ = Group.objects.get_or_create(
            name="Administrator"
        )

        staff_group, _ = Group.objects.get_or_create(
            name="Farm Staff"
        )

        self.admin_user = User.objects.create_user(
            username="sales_admin",
            password="TestPassword123!"
        )

        self.staff_user = User.objects.create_user(
            username="sales_staff",
            password="TestPassword123!"
        )

        self.other_user = User.objects.create_user(
            username="sales_other",
            password="TestPassword123!"
        )

        self.admin_user.groups.add(admin_group)
        self.staff_user.groups.add(staff_group)

        EggStockMovement.objects.create(
            movement_type="HARVEST",
            eggs=1500,
            reference="TEST-SALES-PERMISSIONS"
        )

        record_sale(
            recorded_by=self.admin_user,
            product_type="FULL_TRAY",
            quantity=2,
            unit_price=Decimal("123.45")
        )

    def test_administrator_can_view_revenue(self):

        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Total Sales Revenue"
        )

        self.assertIn(
            "total_revenue",
            response.context
        )

    def test_farm_staff_cannot_view_revenue(self):

        self.client.force_login(self.staff_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertNotContains(
            response,
            "Total Sales Revenue"
        )

        self.assertNotIn(
            "total_revenue",
            response.context
        )

        self.assertNotContains(
            response,
            "<th>Revenue</th>",
            html=True
        )

        self.assertNotContains(
            response,
            "<th>Unit Price</th>",
            html=True
        )

    def test_farm_staff_can_view_sales_quantities(self):

        self.client.force_login(self.staff_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Recent Sales"
        )

        self.assertContains(
            response,
            "Eggs Sold"
        )

        self.assertEqual(
            response.context["recent_sales"][0]["quantity"],
            2
        )

        self.assertNotIn(
            "total_amount",
            response.context["recent_sales"][0]
        )

        self.assertNotIn(
            "unit_price",
            response.context["recent_sales"][0]
        )

    def test_unassigned_user_cannot_access_sales(self):

        self.client.force_login(self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

from datetime import date

from django.test import override_settings
from django.utils import timezone
from unittest.mock import patch


class SalesLockingTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="locking_test_user",
            password="TestPassword123!"
        )

        EggStockMovement.objects.create(
            movement_type="HARVEST",
            eggs=1500,
            reference="LOCKING-TEST"
        )

    @override_settings(TIME_ZONE="Africa/Douala")
    def test_current_day_sale_is_unlocked(self):

        sale = record_sale(
            recorded_by=self.user,
            product_type="FULL_TRAY",
            quantity=1,
            unit_price=Decimal("10.00")
        )

        self.assertFalse(sale.is_locked)

    @override_settings(TIME_ZONE="Africa/Douala")
    def test_previous_day_sale_is_locked(self):

        sale = record_sale(
            recorded_by=self.user,
            product_type="FULL_TRAY",
            quantity=1,
            unit_price=Decimal("10.00")
        )

        sale.business_date = date(2020, 1, 1)
        sale.save(update_fields=["business_date"])

        self.assertTrue(sale.is_locked)

    @override_settings(TIME_ZONE="Africa/Douala")
    def test_sale_locks_at_cameroon_midnight(self):

        from datetime import datetime, timezone as dt_timezone

        sale = record_sale(
            recorded_by=self.user,
            product_type="FULL_TRAY",
            quantity=1,
            unit_price=Decimal("10.00")
        )

        sale.business_date = date(2026, 10, 11)
        sale.save(update_fields=["business_date"])

        # 22:59 UTC = 23:59 Cameroon time.
        before_midnight = datetime(
            2026, 10, 11, 22, 59,
            tzinfo=dt_timezone.utc
        )

        # 23:00 UTC = 00:00 on October 12
        # in Cameroon.
        at_midnight = datetime(
            2026, 10, 11, 23, 0,
            tzinfo=dt_timezone.utc
        )

        with patch(
            "django.utils.timezone.now",
            return_value=before_midnight
        ):
            self.assertFalse(sale.is_locked)

        with patch(
            "django.utils.timezone.now",
            return_value=at_midnight
        ):
            self.assertTrue(sale.is_locked)

class SaleCorrectionTests(TestCase):

    def setUp(self):
        from django.contrib.auth.models import Group

        self.admin_user = get_user_model().objects.create_user(
            username="correction_admin",
            password="TestPassword123!"
        )

        self.staff_user = get_user_model().objects.create_user(
            username="correction_staff",
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

        EggStockMovement.objects.create(
            movement_type="HARVEST",
            eggs=300,
            reference="CORRECTION-TEST-HARVEST",
        )

        self.sale = record_sale(
            recorded_by=self.staff_user,
            product_type="FULL_TRAY",
            quantity=5,
            unit_price=Decimal("10.00"),
        )

    def test_administrator_can_correct_sale(self):

        correction = correct_sale(
            sale_id=self.sale.id,
            corrected_by=self.admin_user,
            reason="Customer purchased four trays",
            product_type="FULL_TRAY",
            quantity=4,
            unit_price=Decimal("10.00"),
        )

        self.sale.refresh_from_db()

        self.assertEqual(self.sale.quantity, 4)
        self.assertEqual(self.sale.eggs_sold, 120)
        self.assertEqual(
            self.sale.total_amount,
            Decimal("40.00")
        )

        self.assertEqual(
            EggStockMovement.current_stock(),
            180
        )

        self.assertEqual(correction.old_quantity, 5)
        self.assertEqual(correction.new_quantity, 4)

    def test_staff_cannot_correct_sale(self):

        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            correct_sale(
                sale_id=self.sale.id,
                corrected_by=self.staff_user,
                reason="Unauthorized correction",
                product_type="FULL_TRAY",
                quantity=4,
                unit_price=Decimal("10.00"),
            )

        self.sale.refresh_from_db()
        self.assertEqual(self.sale.quantity, 5)

    def test_correction_requires_reason(self):

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            correct_sale(
                sale_id=self.sale.id,
                corrected_by=self.admin_user,
                reason="",
                product_type="FULL_TRAY",
                quantity=4,
                unit_price=Decimal("10.00"),
            )

    def test_correction_cannot_overdraw_inventory(self):

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            correct_sale(
                sale_id=self.sale.id,
                corrected_by=self.admin_user,
                reason="Increase quantity",
                product_type="FULL_TRAY",
                quantity=20,
                unit_price=Decimal("10.00"),
            )

        self.sale.refresh_from_db()

        self.assertEqual(self.sale.quantity, 5)
        self.assertEqual(
            EggStockMovement.current_stock(),
            150
        )

        self.assertEqual(
            SaleCorrection.objects.count(),
            0
        )

    def test_correction_preserves_audit_history(self):

        correct_sale(
            sale_id=self.sale.id,
            corrected_by=self.admin_user,
            reason="Price correction",
            product_type="FULL_TRAY",
            quantity=5,
            unit_price=Decimal("12.00"),
        )

        correction = SaleCorrection.objects.get(
            sale=self.sale
        )

        self.assertEqual(
            correction.old_total_amount,
            Decimal("50.00")
        )

        self.assertEqual(
            correction.new_total_amount,
            Decimal("60.00")
        )

        self.assertEqual(
            correction.corrected_by,
            self.admin_user
        )

        self.assertEqual(
            EggStockMovement.current_stock(),
            150
        )

class SalesCorrectionInterfaceTests(TestCase):

    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="interface_admin",
            password="TestPassword123!"
        )

        self.staff_user = get_user_model().objects.create_user(
            username="interface_staff",
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

        EggStockMovement.objects.create(
            movement_type="HARVEST",
            eggs=300,
            reference="INTERFACE-TEST"
        )

        self.sale = record_sale(
            recorded_by=self.staff_user,
            product_type="FULL_TRAY",
            quantity=5,
            unit_price=Decimal("10.00")
        )

        self.list_url = reverse("sales_correction_list")

        self.detail_url = reverse(
            "sales_correction_detail",
            args=[self.sale.id]
        )

    def test_admin_can_view_correction_list(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sales Corrections")

    def test_admin_can_view_correction_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Correct Sale")

    def test_staff_cannot_access_corrections(self):
        self.client.force_login(self.staff_user)

        self.assertEqual(
            self.client.get(self.list_url).status_code,
            403
        )

        self.assertEqual(
            self.client.get(self.detail_url).status_code,
            403
        )

    def test_admin_can_submit_correction(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            self.detail_url,
            {
                "product_type": "FULL_TRAY",
                "quantity": 4,
                "unit_price": "10.00",
                "trays_per_box": "",
                "reason": "Customer purchased four trays",
            }
        )

        self.assertRedirects(response, self.list_url)

        self.sale.refresh_from_db()

        self.assertEqual(self.sale.quantity, 4)

        self.assertEqual(
            EggStockMovement.current_stock(),
            180
        )

        self.assertEqual(
            SaleCorrection.objects.filter(
                sale=self.sale
            ).count(),
            1
        )

    def test_correction_requires_reason(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            self.detail_url,
            {
                "product_type": "FULL_TRAY",
                "quantity": 4,
                "unit_price": "10.00",
                "trays_per_box": "",
                "reason": "",
            }
        )

        self.assertEqual(response.status_code, 200)

        self.sale.refresh_from_db()

        self.assertEqual(self.sale.quantity, 5)

        self.assertEqual(
            SaleCorrection.objects.count(),
            0
        )

    def test_unauthenticated_user_redirected(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 302)

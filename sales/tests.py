from django.test import TestCase

# Create your tests here.

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.models import EggStockMovement
from sales.models import Sale
from sales.services import record_sale


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

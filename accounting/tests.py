from django.test import TestCase

# Create your tests here.
from datetime import timedelta
from django.utils import timezone
from sales.models import Sale
from accounting.views import calculate_finances
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounting.models import Expense


class AccountingTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="accounting_test_user",
            password="TestPassword123!"
        )

        self.client.force_login(self.user)

        self.url = reverse("accounting_dashboard")

    def test_accounting_dashboard_loads(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "accounting/dashboard.html"
        )

    def test_expense_can_be_recorded(self):
        response = self.client.post(
            self.url,
            {
                "business_date": "2026-10-11",
                "category": "FEED",
                "description": "Poultry feed purchase",
                "amount": "250.00",
            }
        )

        self.assertRedirects(response, self.url)

        self.assertEqual(Expense.objects.count(), 1)

        expense = Expense.objects.first()

        self.assertEqual(
            expense.amount,
            Decimal("250.00")
        )

        self.assertEqual(
            expense.recorded_by,
            self.user
        )

    def test_negative_expense_is_rejected(self):
        response = self.client.post(
            self.url,
            {
                "business_date": "2026-10-11",
                "category": "FEED",
                "description": "Invalid expense",
                "amount": "-50.00",
            }
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(Expense.objects.count(), 0)

    def test_expenses_reduce_net_income(self):
        Expense.objects.create(
            business_date=date(2026, 10, 11),
            category="FEED",
            description="Feed purchase",
            amount=Decimal("100.00"),
            recorded_by=self.user,
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.context["total_expenses"],
            Decimal("100.00")
        )

        self.assertEqual(
            response.context["net_profit"],
            response.context["total_revenue"]
            - Decimal("100.00")
        )

class FinancialReportingTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="financial_test_user",
            password="TestPassword123!"
        )

        self.today = timezone.localdate()
        self.yesterday = self.today - timedelta(days=1)

    def create_sale(self, business_date, amount):
        return Sale.objects.create(
            business_date=business_date,
            product_type="FULL_TRAY",
            quantity=1,
            unit_price=amount,
            total_amount=amount,
            eggs_sold=30,
            recorded_by=self.user,
        )

    def create_expense(self, business_date, amount):
        return Expense.objects.create(
            business_date=business_date,
            category="FEED",
            description="Feed purchase",
            amount=amount,
            recorded_by=self.user,
        )

    def test_daily_financial_report(self):

        self.create_sale(
            self.today,
            Decimal("500.00")
        )

        self.create_expense(
            self.today,
            Decimal("200.00")
        )

        report = calculate_finances(
            self.today,
            self.today
        )

        self.assertEqual(
            report["revenue"],
            Decimal("500.00")
        )

        self.assertEqual(
            report["expenses"],
            Decimal("200.00")
        )

        self.assertEqual(
            report["net_income"],
            Decimal("300.00")
        )

    def test_date_filter_excludes_older_records(self):

        self.create_sale(
            self.yesterday,
            Decimal("400.00")
        )

        self.create_sale(
            self.today,
            Decimal("100.00")
        )

        report = calculate_finances(
            self.today,
            self.today
        )

        self.assertEqual(
            report["revenue"],
            Decimal("100.00")
        )

    def test_all_time_financial_report(self):

        self.create_sale(
            self.yesterday,
            Decimal("400.00")
        )

        self.create_sale(
            self.today,
            Decimal("600.00")
        )

        self.create_expense(
            self.today,
            Decimal("250.00")
        )

        report = calculate_finances()

        self.assertEqual(
            report["revenue"],
            Decimal("1000.00")
        )

        self.assertEqual(
            report["expenses"],
            Decimal("250.00")
        )

        self.assertEqual(
            report["net_income"],
            Decimal("750.00")
        )

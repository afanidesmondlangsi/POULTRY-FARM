
from datetime import date, timedelta
from decimal import Decimal
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from accounts.permissions import administrator_required
from sales.models import Sale
from .forms import ExpenseForm
from .models import Expense


def calculate_finances(start_date=None, end_date=None):
    """
    Calculate revenue, expenses, and net income.

    If no dates are provided, calculate all-time totals.
    """

    sales = Sale.objects.all()
    expenses = Expense.objects.all()

    if start_date is not None:
        sales = sales.filter(business_date__gte=start_date)
        expenses = expenses.filter(business_date__gte=start_date)

    if end_date is not None:
        sales = sales.filter(business_date__lte=end_date)
        expenses = expenses.filter(business_date__lte=end_date)

    revenue = (
        sales.aggregate(total=Sum("total_amount"))["total"]
        or Decimal("0.00")
    )

    expense_total = (
        expenses.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    return {
        "revenue": revenue,
        "expenses": expense_total,
        "net_income": revenue - expense_total,
    }


@administrator_required
def accounting_dashboard(request):

    if request.method == "POST":

        form = ExpenseForm(request.POST)

        if form.is_valid():
            expense = form.save(commit=False)
            expense.recorded_by = request.user
            expense.save()

            messages.success(
                request,
                "Expense recorded successfully."
            )

            return redirect("accounting_dashboard")

    else:
        form = ExpenseForm()

    today = timezone.localdate()

    # Week begins on Monday
    week_start = today - timedelta(days=today.weekday())

    # Month begins on the first day
    month_start = today.replace(day=1)

    # Year begins on January 1
    year_start = today.replace(month=1, day=1)

    # All-time financial totals
    all_time = calculate_finances()

    # Daily financial totals
    daily = calculate_finances(today, today)

    # Weekly financial totals
    weekly = calculate_finances(week_start, today)

    # Monthly financial totals
    monthly = calculate_finances(month_start, today)

    # Yearly financial totals
    yearly = calculate_finances(year_start, today)

    
    # Financial performance reporting periods
    chart_data = {}

    # Daily charts: last 7 and 30 days
    for period in (7, 30):

        labels = []
        revenues = []
        expenses = []
        net_incomes = []

        for days_ago in range(period - 1, -1, -1):
            report_date = today - timedelta(days=days_ago)

            finances = calculate_finances(
                report_date,
                report_date
            )

            labels.append(report_date.strftime("%d %b"))
            revenues.append(float(finances["revenue"]))
            expenses.append(float(finances["expenses"]))
            net_incomes.append(float(finances["net_income"]))

        chart_data[str(period)] = {
            "labels": labels,
            "revenue": revenues,
            "expenses": expenses,
            "net_income": net_incomes,
        }

    # Monthly chart: last 12 calendar months
    labels = []
    revenues = []
    expenses = []
    net_incomes = []

    for months_ago in range(11, -1, -1):

        month_index = (
            today.year * 12
            + today.month - 1
            - months_ago
        )

        year = month_index // 12
        month = month_index % 12 + 1

        start_date = date(year, month, 1)

        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        end_date = min(
            next_month - timedelta(days=1),
            today
        )

        finances = calculate_finances(
            start_date,
            end_date
        )

        labels.append(start_date.strftime("%b %Y"))
        revenues.append(float(finances["revenue"]))
        expenses.append(float(finances["expenses"]))
        net_incomes.append(float(finances["net_income"]))

    chart_data["12months"] = {
        "labels": labels,
        "revenue": revenues,
        "expenses": expenses,
        "net_income": net_incomes,
    }


    recent_expenses = Expense.objects.select_related(
        "recorded_by"
    ).order_by(
        "-business_date", "-created_at"
    )[:10]

    context = {
        "form": form,

        # Keep existing dashboard variables
        "total_revenue": all_time["revenue"],
        "total_expenses": all_time["expenses"],
        "net_profit": all_time["net_income"],

        # New reporting variables
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "yearly": yearly,

        "today": today,
        "week_start": week_start,
        "month_start": month_start,
        "year_start": year_start,

        "recent_expenses": recent_expenses,
        "chart_data": json.dumps(chart_data),
    }

    return render(
        request,
        "accounting/dashboard.html",
        context
    )

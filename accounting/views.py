
from datetime import date, timedelta
from decimal import Decimal
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

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


@login_required
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

    # Financial performance for the last 7 days
    chart_labels = []
    chart_revenue = []
    chart_expenses = []
    chart_net_income = []

    for days_ago in range(6, -1, -1):
        report_date = today - timedelta(days=days_ago)

        finances = calculate_finances(
            report_date,
            report_date
        )

        chart_labels.append(
            report_date.strftime("%d %b")
        )

        chart_revenue.append(
            float(finances["revenue"])
        )

        chart_expenses.append(
            float(finances["expenses"])
        )

        chart_net_income.append(
            float(finances["net_income"])
        )

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
        "chart_labels": json.dumps(chart_labels),
        "chart_revenue": json.dumps(chart_revenue),
        "chart_expenses": json.dumps(chart_expenses),
        "chart_net_income": json.dumps(chart_net_income),
    }

    return render(
        request,
        "accounting/dashboard.html",
        context
    )

import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import TableForm, TransactionFilterForm, TransactionForm
from .models import Category, Table, Transaction
from .services.currency_converter import CurrencyConverter

# === TABLE VIEWS ===


class TableListView(LoginRequiredMixin, ListView):
    """Display list of tables for current user"""

    model = Table
    template_name = "finances/table_list.html"
    context_object_name = "tables"

    def get_queryset(self):
        # Return only tables belonging to current user
        return Table.objects.filter(user=self.request.user)


class TableCreateView(LoginRequiredMixin, CreateView):
    """Create new table"""

    model = Table
    form_class = TableForm
    template_name = "finances/table_form.html"
    success_url = reverse_lazy("finances:table_list")

    def form_valid(self, form):
        # Set current user as table owner
        form.instance.user = self.request.user
        messages.success(self.request, "Таблицю успішно створено!")
        return super().form_valid(form)


class TableUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update existing table"""

    model = Table
    form_class = TableForm
    template_name = "finances/table_form.html"
    success_url = reverse_lazy("finances:table_list")

    def test_func(self):
        # Check if user owns the table
        table = self.get_object()
        return self.request.user == table.user

    def form_valid(self, form):
        messages.success(self.request, "Таблицю успішно оновлено!")
        return super().form_valid(form)


class TableDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete table"""

    model = Table
    template_name = "finances/table_confirm_delete.html"
    success_url = reverse_lazy("finances:table_list")

    def test_func(self):
        # Check if user owns the table
        table = self.get_object()
        return self.request.user == table.user

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Таблицю успішно видалено!")
        return super().delete(request, *args, **kwargs)


# === TRANSACTION VIEWS ===


class TransactionListView(LoginRequiredMixin, ListView):
    """Display and filter transactions"""

    model = Transaction
    template_name = "finances/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 20

    def get_queryset(self):
        # Get transactions for current user with related data
        user = self.request.user
        queryset = Transaction.objects.filter(table__user=user).select_related("table", "category", "category__parent")

        # Apply filters from form
        form = TransactionFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get("search")
            date_from = form.cleaned_data.get("date_from")
            date_to = form.cleaned_data.get("date_to")
            category = form.cleaned_data.get("category")
            subcategory = form.cleaned_data.get("subcategory")
            currency = form.cleaned_data.get("currency")

            if search:
                queryset = queryset.filter(table__title__icontains=search)
            if date_from:
                queryset = queryset.filter(date__gte=date_from)
            if date_to:
                queryset = queryset.filter(date__lte=date_to)
            if subcategory:
                queryset = queryset.filter(category=subcategory)
            elif category:
                # Include both category and its subcategories
                queryset = queryset.filter(Q(category=category) | Q(category__parent=category))
            if currency:
                queryset = queryset.filter(currency=currency)

        return queryset.order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter form to context
        context["filter_form"] = TransactionFilterForm(self.request.GET)

        # Prepare category hierarchy for template
        main_categories = Category.objects.filter(parent__isnull=True)
        categories_hierarchy = []

        for main_cat in main_categories:
            children = main_cat.children.all()
            categories_hierarchy.append(
                {"name": main_cat.name, "children": [{"name": child.name, "id": child.id} for child in children]}
            )

        context["categories_hierarchy"] = categories_hierarchy

        # Calculate transaction statistics
        queryset = self.get_queryset()
        context["total_count"] = queryset.count()

        # Calculate totals per currency
        totals = queryset.values("currency").annotate(total=Sum("amount"))
        context["currency_totals"] = {item["currency"]: item["total"] for item in totals}

        # Prepare transaction data for JavaScript
        context["transaction_amounts"] = [
            {
                "amount": transaction.amount,
                "currency": transaction.currency,
                "id": transaction.id,
                "category": (
                    {
                        "name": transaction.category.name if transaction.category else "Без категорії",
                        "parent_name": (
                            transaction.category.parent.name
                            if transaction.category and transaction.category.parent
                            else None
                        ),
                    }
                    if transaction.category
                    else None
                ),
            }
            for transaction in context["transactions"]
        ]

        # Calculate total amount across all currencies
        if context["currency_totals"]:
            context["total_amount_all"] = sum(context["currency_totals"].values())
        else:
            context["total_amount_all"] = 0

        # Handle currency conversion if requested
        convert_to = self.request.GET.get("convert_to")
        if convert_to and convert_to in ["UAH", "USD", "EUR"]:
            context["target_currency"] = convert_to
            context["converted_transaction_amounts"] = []
            total_converted = 0

            for transaction in context["transactions"]:
                amount = float(transaction.amount)
                currency = transaction.currency

                if currency == convert_to:
                    converted_amount = amount
                else:
                    converted_amount = CurrencyConverter.convert_amount(amount, currency, convert_to) or amount

                context["converted_transaction_amounts"].append(
                    {
                        "original_amount": amount,
                        "original_currency": currency,
                        "converted_amount": round(converted_amount, 2),
                        "target_currency": convert_to,
                        "id": transaction.id,
                    }
                )
                total_converted += converted_amount

            context["total_converted"] = round(total_converted, 2)

        return context

    @staticmethod
    def convert_all_to_currency(currency_totals, target_currency="UAH"):
        """Convert currency totals to target currency"""
        converted = {}
        total_converted = 0

        for currency, amount in currency_totals.items():
            if currency == target_currency:
                converted_amount = float(amount)
            else:
                converted_amount = CurrencyConverter.convert_amount(float(amount), currency, target_currency)
                if converted_amount is None:
                    continue

            converted[f"{currency}_to_{target_currency}"] = round(converted_amount, 2)
            total_converted += converted_amount

        converted[f"total_{target_currency.lower()}"] = round(total_converted, 2)
        converted["total"] = round(total_converted, 2)

        return converted


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create new transaction"""

    model = Transaction
    form_class = TransactionForm
    template_name = "finances/transaction_form.html"

    def get_form_kwargs(self):
        # Pass user to form for table filtering
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Prepare category hierarchy for dropdown
        main_categories = Category.objects.filter(parent__isnull=True)
        categories_hierarchy = []

        for main_cat in main_categories:
            children = main_cat.children.all()
            categories_hierarchy.append(
                {
                    "id": main_cat.id,
                    "name": main_cat.name,
                    "children": [
                        {
                            "id": child.id,
                            "name": child.name,
                        }
                        for child in children
                    ],
                }
            )

        context["categories_hierarchy"] = categories_hierarchy
        return context

    def form_valid(self, form):
        messages.success(self.request, "Транзакцію успішно додано!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("finances:transaction_list")


class TransactionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update existing transaction"""

    model = Transaction
    form_class = TransactionForm
    template_name = "finances/transaction_form.html"

    def test_func(self):
        # Check if user owns the transaction's table
        transaction = self.get_object()
        return self.request.user == transaction.table.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        # Same as create view for category hierarchy
        context = super().get_context_data(**kwargs)

        main_categories = Category.objects.filter(parent__isnull=True)
        categories_hierarchy = []

        for main_cat in main_categories:
            children = main_cat.children.all()
            categories_hierarchy.append(
                {
                    "id": main_cat.id,
                    "name": main_cat.name,
                    "children": [
                        {
                            "id": child.id,
                            "name": child.name,
                        }
                        for child in children
                    ],
                }
            )

        context["categories_hierarchy"] = categories_hierarchy
        return context

    def form_valid(self, form):
        messages.success(self.request, "Транзакцію успішно оновлено!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("finances:transaction_list")


class TransactionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete transaction"""

    model = Transaction
    template_name = "finances/transaction_confirm_delete.html"
    success_url = reverse_lazy("finances:transaction_list")

    def test_func(self):
        # Check if user owns the transaction's table
        transaction = self.get_object()
        return self.request.user == transaction.table.user

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Транзакцію успішно видалено!")
        return super().delete(request, *args, **kwargs)


# === DASHBOARD VIEW ===


@login_required
def dashboard(request):
    """Main dashboard with recent transactions and totals"""
    user = request.user

    # Get recent transactions
    recent_transactions = Transaction.objects.filter(table__user=user).select_related(
        "table", "category", "category__parent"
    )[:5]

    # Calculate total expenses converted to UAH
    all_transactions = Transaction.objects.filter(table__user=user)
    total_in_uah = 0

    for transaction in all_transactions:
        amount = float(transaction.amount)
        currency = transaction.currency

        if currency == "UAH":
            total_in_uah += amount
        else:
            converted = CurrencyConverter.convert_amount(amount, currency, "UAH")
            if converted:
                total_in_uah += converted

    total_expenses = round(total_in_uah, 2)

    context = {
        "recent_transactions": recent_transactions,
        "total_expenses": total_expenses,
        "tables": Table.objects.filter(user=user),
    }

    return render(request, "finances/dashboard.html", context)


# === CURRENCY CONVERTER VIEW ===


@login_required
def currency_converter(request):
    """Currency conversion tool"""
    if request.method == "POST":
        # Handle conversion request
        amount = request.POST.get("amount", "0")
        from_currency = request.POST.get("from_currency", "UAH")
        to_currency = request.POST.get("to_currency", "USD")

        converted_amount = CurrencyConverter.convert_amount(amount, from_currency, to_currency)

        return JsonResponse(
            {"success": converted_amount is not None, "converted_amount": converted_amount, "currency": to_currency}
        )

    # GET request - display converter
    supported_currencies = CurrencyConverter.get_supported_currencies()

    # Get current exchange rates
    rates = CurrencyConverter.get_exchange_rates()
    exchange_rates = {}
    if rates:
        exchange_rates = {
            "USD": rates.get("USD", 1),
            "EUR": rates.get("EUR", 1),
            "UAH": rates.get("UAH", 1),
        }

    return render(
        request,
        "finances/currency_converter.html",
        {
            "currencies": supported_currencies,
            "exchange_rates": exchange_rates,
        },
    )


class AnalyticsView(LoginRequiredMixin, TemplateView):
    """Financial analytics and statistics view"""

    template_name = "finances/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get period filter
        period = self.request.GET.get("period", "30")

        # Get transactions for current user
        transactions = Transaction.objects.filter(table__user=self.request.user).select_related("table", "category")

        # Apply period filter if not 'all'
        if period != "all":
            days = int(period)
            start_date = timezone.now() - timedelta(days=days)
            transactions = transactions.filter(date__gte=start_date)

        # Convert all amounts to UAH for consistent analysis
        converted_data = []
        total_amount_uah = 0
        max_amount_uah = 0

        for t in transactions:
            amount_uah = CurrencyConverter.convert_amount(t.amount, t.currency, "UAH") or float(t.amount)

            converted_data.append(
                {
                    "transaction": t,
                    "amount_uah": amount_uah,
                    "category": t.category,
                    "table": t.table,
                    "currency": t.currency,
                    "date": t.date,
                }
            )

            total_amount_uah += amount_uah
            max_amount_uah = max(max_amount_uah, amount_uah)

        # Calculate basic statistics
        count = len(converted_data)
        average_amount_uah = total_amount_uah / count if count > 0 else 0

        # Category statistics
        category_stats_dict = {}
        for data in converted_data:
            category = data["category"]
            if not category:
                continue

            # Use parent category for grouping
            parent_cat = category.parent if category.parent else category
            cat_name = parent_cat.name

            if cat_name not in category_stats_dict:
                category_stats_dict[cat_name] = {"total": 0, "count": 0}

            category_stats_dict[cat_name]["total"] += data["amount_uah"]
            category_stats_dict[cat_name]["count"] += 1

        # Prepare category data for chart
        category_stats = []
        category_labels = []
        category_data = []
        colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#C9CBCF", "#43e97b"]

        sorted_categories = sorted(category_stats_dict.items(), key=lambda x: x[1]["total"], reverse=True)

        for i, (cat_name, data) in enumerate(sorted_categories):
            percentage = (data["total"] / total_amount_uah * 100) if total_amount_uah > 0 else 0
            category_stats.append(
                {
                    "name": cat_name,
                    "total": round(data["total"], 2),
                    "count": data["count"],
                    "average": round(data["total"] / data["count"], 2) if data["count"] > 0 else 0,
                    "percentage": round(percentage, 1),
                    "color": colors[i % len(colors)],
                }
            )
            category_labels.append(cat_name)
            category_data.append(round(data["total"], 2))

        # Monthly statistics
        monthly_stats = {}
        for data in converted_data:
            month_key = data["date"].strftime("%Y-%m")
            monthly_stats[month_key] = monthly_stats.get(month_key, 0) + data["amount_uah"]

        sorted_months = sorted(monthly_stats.items())
        monthly_labels = [datetime.strptime(k, "%Y-%m").strftime("%b %Y") for k, _ in sorted_months]
        monthly_data = [round(v, 2) for _, v in sorted_months]

        # Currency statistics
        currency_stats = {}
        for data in converted_data:
            currency = data["currency"]
            currency_stats[currency] = currency_stats.get(currency, 0) + float(data["transaction"].amount)

        currency_labels = [dict(Transaction.CURRENCY_CHOICES).get(k, k) for k in currency_stats.keys()]
        currency_data = [round(v, 2) for v in currency_stats.values()]

        # Table statistics
        table_stats = {}
        for data in converted_data:
            table_name = data["table"].title
            table_stats[table_name] = table_stats.get(table_name, 0) + data["amount_uah"]

        table_labels = list(table_stats.keys())
        table_data = [round(v, 2) for v in table_stats.values()]

        # Add all data to context
        context.update(
            {
                "period": period,
                "total_amount": round(total_amount_uah, 2),
                "average_amount": round(average_amount_uah, 2),
                "max_amount": round(max_amount_uah, 2),
                "category_count": len(category_stats),
                "category_stats": category_stats,
                "category_labels": json.dumps(category_labels),
                "category_data": json.dumps(category_data),
                "monthly_labels": json.dumps(monthly_labels),
                "monthly_data": json.dumps(monthly_data),
                "currency_labels": json.dumps(currency_labels),
                "currency_data": json.dumps(currency_data),
                "table_labels": json.dumps(table_labels),
                "table_data": json.dumps(table_data),
                "transaction_count": count,
            }
        )

        return context

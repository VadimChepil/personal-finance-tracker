from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import Table, Transaction, Category
from .forms import TableForm, TransactionForm, TransactionFilterForm

from .services.currency_converter import CurrencyConverter


# === TABLE VIEWS ===

class TableListView(LoginRequiredMixin, ListView):
    model = Table
    template_name = 'finances/table_list.html'
    context_object_name = 'tables'
    
    def get_queryset(self):
        return Table.objects.filter(user=self.request.user)


class TableCreateView(LoginRequiredMixin, CreateView):
    model = Table
    form_class = TableForm
    template_name = 'finances/table_form.html'
    success_url = reverse_lazy('finances:table_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Таблицю успішно створено!')
        return super().form_valid(form)


class TableUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Table
    form_class = TableForm
    template_name = 'finances/table_form.html'
    success_url = reverse_lazy('finances:table_list')
    
    def test_func(self):
        table = self.get_object()
        return self.request.user == table.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Таблицю успішно оновлено!')
        return super().form_valid(form)


class TableDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Table
    template_name = 'finances/table_confirm_delete.html'
    success_url = reverse_lazy('finances:table_list')
    
    def test_func(self):
        table = self.get_object()
        return self.request.user == table.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Таблицю успішно видалено!')
        return super().delete(request, *args, **kwargs)


# === TRANSACTION VIEWS ===

class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'finances/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(table__user=user).select_related('table').prefetch_related('categories')
        
        form = TransactionFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            category = form.cleaned_data.get('category')
            currency = form.cleaned_data.get('currency')
            
            if search:
                queryset = queryset.filter(table__title__icontains=search)
            if date_from:
                queryset = queryset.filter(date__gte=date_from)
            if date_to:
                queryset = queryset.filter(date__lte=date_to)
            if category:
                queryset = queryset.filter(categories=category)
            if currency:
                queryset = queryset.filter(currency=currency)
        
        return queryset.order_by('-date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        

        context['filter_form'] = TransactionFilterForm(self.request.GET)
        context['categories'] = Category.objects.all() 
        

        queryset = self.get_queryset()
        context['total_count'] = queryset.count()
        

        totals = queryset.values('currency').annotate(total=Sum('amount'))
        context['currency_totals'] = {item['currency']: item['total'] for item in totals}
        
        context['transaction_amounts'] = [
            {
                'amount': transaction.amount,
                'currency': transaction.currency,
                'id': transaction.id  
            }
            for transaction in context['transactions']  
        ]
        
        if context['currency_totals']:
            context['total_amount_all'] = sum(context['currency_totals'].values())
        else:
            context['total_amount_all'] = 0
        
        convert_to = self.request.GET.get('convert_to')
        if convert_to and convert_to in ['UAH', 'USD', 'EUR']:
            context['target_currency'] = convert_to
        
            context['converted_transaction_amounts'] = []
            total_converted = 0
            
            for transaction in context['transactions']:
                amount = float(transaction.amount)
                currency = transaction.currency
                
                if currency == convert_to:
                    converted_amount = amount
                else:
                    converted_amount = CurrencyConverter.convert_amount(
                        amount, 
                        currency, 
                        convert_to
                    ) or amount  
                
                context['converted_transaction_amounts'].append({
                    'original_amount': amount,
                    'original_currency': currency,
                    'converted_amount': round(converted_amount, 2),
                    'target_currency': convert_to,
                    'id': transaction.id
                })
                total_converted += converted_amount
            
            context['total_converted'] = round(total_converted, 2)
        
        return context
        
    @staticmethod    
    def convert_all_to_currency(currency_totals, target_currency='UAH'):
        converted = {}
        total_converted = 0
        
        for currency, amount in currency_totals.items():
            if currency == target_currency:
                converted_amount = float(amount)
            else:
                converted_amount = CurrencyConverter.convert_amount(
                    float(amount), 
                    currency, 
                    target_currency
                )
                if converted_amount is None:
                    continue
            
            converted[f'{currency}_to_{target_currency}'] = round(converted_amount, 2)
            total_converted += converted_amount
        
        converted[f'total_{target_currency.lower()}'] = round(total_converted, 2)
        converted['total'] = round(total_converted, 2)
        
        return converted

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'finances/transaction_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Транзакцію успішно додано!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('finances:transaction_list')


class TransactionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'finances/transaction_form.html'
    
    def test_func(self):
        transaction = self.get_object()
        return self.request.user == transaction.table.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Транзакцію успішно оновлено!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('finances:transaction_list')


class TransactionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Transaction
    template_name = 'finances/transaction_confirm_delete.html'
    success_url = reverse_lazy('finances:transaction_list')
    
    def test_func(self):
        transaction = self.get_object()
        return self.request.user == transaction.table.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Транзакцію успішно видалено!')
        return super().delete(request, *args, **kwargs)


# === DASHBOARD VIEW ===

@login_required
def dashboard(request):
    user = request.user
    
    recent_transactions = Transaction.objects.filter(
        table__user=user
    ).select_related('table').prefetch_related('categories')[:5]
    
    all_transactions = Transaction.objects.filter(table__user=user)
    total_in_uah = 0

    for transaction in all_transactions:
        amount = float(transaction.amount)
        currency = transaction.currency
        
        if currency == 'UAH':
            total_in_uah += amount
        else:
            converted = CurrencyConverter.convert_amount(amount, currency, 'UAH')
            if converted:
                total_in_uah += converted

    total_expenses = round(total_in_uah, 2)  

    context = {
        'recent_transactions': recent_transactions,
        'total_expenses': total_expenses,
        'tables': Table.objects.filter(user=user),
    }
    
    return render(request, 'finances/dashboard.html', context)


# === CURRENCU_CONVERTER VIEW ===

@login_required
def currency_converter(request):
    """Сторінка конвертації валют"""
    if request.method == 'POST':
        amount = request.POST.get('amount', '0')
        from_currency = request.POST.get('from_currency', 'UAH')
        to_currency = request.POST.get('to_currency', 'USD')
        
        converted_amount = CurrencyConverter.convert_amount(amount, from_currency, to_currency)
        
        return JsonResponse({
            'success': converted_amount is not None,
            'converted_amount': converted_amount,
            'currency': to_currency
        })
    

    supported_currencies = CurrencyConverter.get_supported_currencies()
    
  
    rates = CurrencyConverter.get_exchange_rates()
    exchange_rates = {}
    if rates:
        exchange_rates = {
            'USD': rates.get('USD', 1),
            'EUR': rates.get('EUR', 1),
            'UAH': rates.get('UAH', 1),
        }
    
    return render(request, 'finances/currency_converter.html', {
        'currencies': supported_currencies,
        'exchange_rates': exchange_rates,
    })
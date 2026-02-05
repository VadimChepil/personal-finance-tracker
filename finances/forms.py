from django import forms
from .models import Table, Transaction, Category
from django.utils import timezone


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['title', 'color']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть назву таблиці'
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control-color',
                'style': 'width: 50px; height: 38px;'
            })
        }
        labels = {
            'title': 'Назва таблиці',
            'color': 'Колір'
        }


class TransactionForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        label='Категорії'
    )
    
    class Meta:
        model = Transaction
        fields = ['table', 'amount', 'currency', 'date', 'description', 'categories']  
        widgets = {
            'table': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '1.00',
                'min': '0'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'value': timezone.now().date()
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис транзакції (необов\'язково)'
            })
        }
        labels = {
            'table': 'Таблиця',
            'amount': 'Сума',
            'currency': 'Валюта',
            'date': 'Дата',
            'description': 'Опис'
        }
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['table'].queryset = Table.objects.filter(user=user)
            self.fields['table'].required = True
            self.fields['table'].empty_label = "Оберіть таблицю"


class TransactionFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пошук по назві...'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Від'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='До'
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Категорія'
    )
    currency = forms.ChoiceField(
        choices=[('', 'Всі валюти')] + Transaction.CURRENCY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Валюта'
    )
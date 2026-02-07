from django import forms
from django.utils import timezone

from .models import Category, Table, Transaction


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ["title", "color"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введіть назву таблиці"}),
            "color": forms.TextInput(
                attrs={"type": "color", "class": "form-control-color", "style": "width: 50px; height: 38px;"}
            ),
        }
        labels = {"title": "Назва таблиці", "color": "Колір"}


class TransactionForm(forms.ModelForm):
    category_id = forms.CharField(required=False, widget=forms.HiddenInput(), initial="")

    class Meta:
        model = Transaction
        fields = ["table", "amount", "currency", "date", "description", "category_id"]
        widgets = {
            "table": forms.Select(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "0.00", "step": "1.00", "min": "0"}
            ),
            "currency": forms.Select(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date", "value": timezone.now().date()}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Опис транзакції (необов'язково)"}
            ),
        }
        labels = {"table": "Таблиця", "amount": "Сума", "currency": "Валюта", "date": "Дата", "description": "Опис"}

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["table"].queryset = Table.objects.filter(user=user)
            self.fields["table"].required = True
            self.fields["table"].empty_label = "Оберіть таблицю"

        if self.instance and self.instance.category:
            self.fields["category_id"].initial = str(self.instance.category.id)

    def save(self, commit=True):
        instance = super().save(commit=False)

        category_id = self.cleaned_data.get("category_id")

        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                instance.category = category
            except Category.DoesNotExist:
                instance.category = None
        else:
            instance.category = None

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class TransactionFilterForm(forms.Form):
    search = forms.CharField(required=False)
    date_from = forms.DateField(required=False)
    date_to = forms.DateField(required=False)

    category = forms.ModelChoiceField(queryset=Category.objects.filter(parent__isnull=True), required=False)

    subcategory = forms.ModelChoiceField(queryset=Category.objects.filter(parent__isnull=False), required=False)

    currency = forms.ChoiceField(choices=[("", "Всі валюти")] + Transaction.CURRENCY_CHOICES, required=False)

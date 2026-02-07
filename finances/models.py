from django.conf import settings
from django.db import models
from django.utils import timezone


class Table(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tables", verbose_name="Користувач"
    )
    title = models.CharField(max_length=100, verbose_name="Назва таблиці")
    color = models.CharField(
        max_length=7, default="#3B82F6", help_text="Колір у форматі HEX (#RRGGBB)", verbose_name="Колір"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        verbose_name = "Таблиця"
        verbose_name_plural = "Таблиці"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user.email})"


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва категорії")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
        verbose_name="Батьківська категорія",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["name", "parent"], name="unique_category_name_parent")]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    @property
    def level(self):
        if self.parent:
            return self.parent.level + 1
        return 0

    @property
    def is_root(self):
        return self.parent is None

    def get_full_path(self):
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " → ".join(path)


class Transaction(models.Model):
    CURRENCY_CHOICES = [
        ("UAH", "Гривня (₴)"),
        ("USD", "Долар США ($)"),
        ("EUR", "Євро (€)"),
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сума")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="UAH", verbose_name="Валюта")
    date = models.DateField(default=timezone.now, verbose_name="Дата транзакції")
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="transactions", verbose_name="Таблиця")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
        blank=True,
        verbose_name="Категорія",
    )
    description = models.TextField(blank=True, verbose_name="Опис транзакції")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")

    class Meta:
        verbose_name = "Транзакція"
        verbose_name_plural = "Транзакції"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.amount} {self.currency} - {self.date}"


def create_default_categories(apps, schema_editor):
    Category = apps.get_model("finances", "Category")

    default_categories = [
        {
            "name": "Продукти",
            "children": [
                {"name": "Супермаркет"},
                {"name": "Ринок"},
                {"name": "М'ясо"},
                {"name": "Овочі/Фрукти"},
            ],
        },
        {
            "name": "Транспорт",
            "children": [
                {"name": "Пальне"},
                {"name": "Ремонт"},
                {"name": "Страховка"},
                {"name": "Парковка"},
            ],
        },
        {
            "name": "Розваги",
            "children": [
                {"name": "Кіно"},
                {"name": "Ресторани"},
                {"name": "Подорожі"},
                {"name": "Хобі"},
            ],
        },
        {
            "name": "Житло",
            "children": [
                {"name": "Оренда"},
                {"name": "Комунальні"},
                {"name": "Інтернет"},
                {"name": "Меблі"},
            ],
        },
        {
            "name": "Здоров'я",
            "children": [
                {"name": "Ліки"},
                {"name": "Лікар"},
                {"name": "Спорт"},
                {"name": "Страхування"},
            ],
        },
        {
            "name": "Освіта",
            "children": [
                {"name": "Книги"},
                {"name": "Курси"},
                {"name": "Канцелярія"},
                {"name": "Абонементи"},
            ],
        },
        {
            "name": "Одяг",
            "children": [
                {"name": "Взуття"},
                {"name": "Верхній одяг"},
                {"name": "Нижня білизна"},
                {"name": "Аксесуари"},
            ],
        },
        {"name": "Інше", "children": []},
    ]

    for category_data in default_categories:
        parent, created = Category.objects.get_or_create(name=category_data["name"], defaults={})

        for child_data in category_data["children"]:
            Category.objects.get_or_create(name=child_data["name"], parent=parent, defaults={})

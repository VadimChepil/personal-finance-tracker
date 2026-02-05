from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class Table(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tables',
        verbose_name='Користувач'
    )
    title = models.CharField(
        max_length=100,
        verbose_name='Назва таблиці'
    )
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text='Колір у форматі HEX (#RRGGBB)',
        verbose_name='Колір'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )

    class Meta:
        verbose_name = 'Таблиця'
        verbose_name_plural = 'Таблиці'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.user.email})"


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Назва категорії'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Опис категорії'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )

    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        ordering = ['name']

    def __str__(self):
        return self.name


class Transaction(models.Model):
    CURRENCY_CHOICES = [
        ('UAH', 'Гривня (₴)'),
        ('USD', 'Долар США ($)'),
        ('EUR', 'Євро (€)'),
    ]

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сума'
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='UAH',
        verbose_name='Валюта'
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name='Дата транзакції'
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Таблиця'
    )
    categories = models.ManyToManyField(
        Category,
        related_name='transactions',
        blank=True,
        verbose_name='Категорії'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Опис транзакції'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата оновлення'
    )

    class Meta:
        verbose_name = 'Транзакція'
        verbose_name_plural = 'Транзакції'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.amount} {self.currency} - {self.date}"


# Функція для створення дефолтних категорій
def create_default_categories(apps, schema_editor):
    Category = apps.get_model('finances', 'Category')
    
    default_categories = [
        {
            'name': 'Продукти',
            'description': 'Витрати на продукти харчування'
        },
        {
            'name': 'Авто',
            'description': 'Витрати на автомобіль: пальне, ремонт, страховка'
        },
        {
            'name': 'Одяг',
            'description': 'Витрати на одяг та взуття'
        },
        {
            'name': 'Розваги',
            'description': 'Витрати на розваги та відпочинок'
        },
        {
            'name': "Здоров'я",  
            'description': "Витрати на медицину та здоров'я"  
        },
        {
            'name': 'Комунальні',
            'description': 'Оплата комунальних послуг'
        },
        {
            'name': 'Транспорт',
            'description': 'Витрати на громадський транспорт'
        },
        {
            'name': 'Інше',
            'description': 'Інші витрати'
        }
    ]
    
    for category_data in default_categories:
        Category.objects.get_or_create(
            name=category_data['name'],
            defaults={'description': category_data['description']}
        )

@receiver(post_migrate)
def create_default_categories_signal(sender, **kwargs):
    if sender.name == 'finances':
        from django.db import connection
        if 'test' not in connection.settings_dict.get('NAME', ''):
            try:
                create_default_categories = __import__(
                    'finances.migrations.0002_create_default_categories',
                    fromlist=['']
                ).create_default_categories
                
                from django.apps import apps
                create_default_categories(apps, None)
            except (ImportError, AttributeError):
                try:
                    from .models import Category
                    
                    default_categories = [
                        {'name': 'Продукти', 'description': 'Витрати на продукти харчування'},
                        {'name': 'Авто', 'description': 'Витрати на автомобіль: пальне, ремонт, страховка'},
                        {'name': 'Одяг', 'description': 'Витрати на одяг та взуття'},
                    ]
                    
                    for category_data in default_categories:
                        Category.objects.get_or_create(
                            name=category_data['name'],
                            defaults={'description': category_data['description']}
                        )
                except:
                    pass
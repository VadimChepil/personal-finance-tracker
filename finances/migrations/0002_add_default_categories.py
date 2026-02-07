from django.db import migrations


def create_default_categories(apps, schema_editor):
    Category = apps.get_model("finances", "Category")

    default_categories = [
        {"name": "Продукти", "children": ["Супермаркет", "Ринок", "М'ясо", "Овочі/Фрукти"]},
        {"name": "Транспорт", "children": ["Пальне", "Ремонт", "Страховка", "Парковка"]},
        {"name": "Розваги", "children": ["Кіно", "Ресторани", "Подорожі", "Хобі"]},
        {"name": "Житло", "children": ["Оренда", "Комунальні", "Інтернет", "Меблі"]},
        {"name": "Здоров'я", "children": ["Ліки", "Лікар", "Спорт", "Страхування"]},
        {"name": "Освіта", "children": ["Книги", "Курси", "Канцелярія", "Абонементи"]},
        {"name": "Одяг", "children": ["Взуття", "Верхній одяг", "Нижня білизна", "Аксесуари"]},
        {"name": "Інше", "children": []},
    ]

    for category_data in default_categories:
        parent, created = Category.objects.get_or_create(name=category_data["name"])
        for child_name in category_data["children"]:
            Category.objects.get_or_create(name=child_name, parent=parent)


class Migration(migrations.Migration):

    dependencies = [
        ("finances", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_categories),
    ]

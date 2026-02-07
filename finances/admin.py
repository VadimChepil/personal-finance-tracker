from django import forms
from django.contrib import admin
from django.db.models import Q
from django.urls import reverse
from django.utils.html import format_html

from .models import Category, Table, Transaction


# Custom form for Category model with parent-child hierarchy support
class CategoryForm(forms.ModelForm):
    # Field for selecting existing parent category (top-level categories only)
    parent_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent__isnull=True),
        required=False,
        label="Батьківська категорія",
        help_text="Оберіть батьківську категорію зі списку",
    )

    # Field for creating new parent category
    new_parent_category = forms.CharField(
        required=False,
        label="Або створіть нову батьківську категорію",
        help_text="Якщо батьківської категорії немає в списку",
    )

    class Meta:
        model = Category
        fields = ["name"]
        labels = {"name": "Назва підкатегорії"}
        help_texts = {"name": "Введіть назву підкатегорії"}

    def clean(self):
        cleaned_data = super().clean()
        parent_category = cleaned_data.get("parent_category")
        new_parent_category = cleaned_data.get("new_parent_category")
        name = cleaned_data.get("name")

        # Check if required fields are filled
        if not name:
            return cleaned_data

        # Validate: can't select both existing and new parent category
        if parent_category and new_parent_category:
            raise forms.ValidationError("Оберіть лише одне: або існуючу батьківську категорію, або введіть нову")

        # Determine parent category based on form input
        parent = None
        if parent_category:
            parent = parent_category
        elif new_parent_category:
            # Create new parent category if specified
            parent, created = Category.objects.get_or_create(
                name=new_parent_category, parent=None, defaults={"name": new_parent_category}
            )

        # Check for duplicate subcategories
        if parent:
            if Category.objects.filter(name=name, parent=parent).exists():
                raise forms.ValidationError(f"Підкатегорія '{name}' вже існує у категорії '{parent.name}'")
        else:
            # Check for duplicate main categories
            if Category.objects.filter(name=name, parent__isnull=True).exists():
                raise forms.ValidationError(f"Основна категорія '{name}' вже існує")

        cleaned_data["parent"] = parent
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Customize form based on whether editing existing category
        if self.instance and self.instance.pk:
            if self.instance.parent:
                # Editing a subcategory
                self.fields["parent_category"].initial = self.instance.parent
                self.fields["parent_category"].label = "Батьківська категорія"
                self.fields["name"].label = "Назва підкатегорії"
            else:
                # Editing a main category - hide parent fields
                self.fields["parent_category"].widget = forms.HiddenInput()
                self.fields["new_parent_category"].widget = forms.HiddenInput()
                self.fields["name"].label = "Назва категорії"
                self.fields["name"].help_text = "Введіть назву основної категорії"
        else:
            # Creating new category
            self.fields["parent_category"].queryset = Category.objects.filter(parent__isnull=True).order_by("name")
            self.fields["name"].label = "Назва підкатегорії"


# Inline for displaying transactions within Table admin
class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fields = ("amount", "currency", "date", "category", "description")
    show_change_link = True


# Admin configuration for Table model
@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "color", "created_at")
    list_filter = ("user", "created_at")
    search_fields = ("title", "user__email")
    list_select_related = ("user",)
    date_hierarchy = "created_at"
    inlines = [TransactionInline]


# Inline for displaying subcategories within parent category admin
class CategoryInline(admin.TabularInline):
    model = Category
    fk_name = "parent"
    extra = 0
    fields = ("name", "transactions_count", "created_at")
    readonly_fields = ("transactions_count", "created_at")
    show_change_link = True

    def transactions_count(self, obj):
        # Count transactions for this category
        return obj.transactions.count()

    transactions_count.short_description = "Транзакцій"


# Admin configuration for Category model with hierarchical display
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ("parent_or_main_display", "name_display", "subcategories_count", "transactions_count", "created_at")
    list_filter = ("parent", "created_at")
    search_fields = ("name", "parent__name")
    list_select_related = ("parent",)
    inlines = [CategoryInline]

    # Custom admin actions
    actions = ["make_top_level_category"]

    @admin.action(description="Зробити основною категорією")
    def make_top_level_category(self, request, queryset):
        # Action to convert selected categories to top-level
        updated = queryset.update(parent=None)
        self.message_user(request, f"{updated} категорій стало основними")

    def parent_or_main_display(self, obj):
        # Display parent name for subcategories, bold name for main categories
        if obj.parent:
            return obj.parent.name
        else:
            return format_html("<strong>{}</strong>", obj.name)

    parent_or_main_display.short_description = "Батьківська категорія"
    parent_or_main_display.admin_order_field = "parent__name"

    def name_display(self, obj):
        # Display subcategory name or dash for main categories
        if obj.parent:
            return obj.name
        else:
            return "—"

    name_display.short_description = "Підкатегорія"
    name_display.admin_order_field = "name"

    def subcategories_count(self, obj):
        # Count of child categories
        return obj.children.count()

    subcategories_count.short_description = "Кільк. підкатегорій"

    def transactions_count(self, obj):
        # Count of transactions in this category
        return obj.transactions.count()

    transactions_count.short_description = "Кільк. транзакцій"

    # Form layout with two sections
    fieldsets = (
        (
            "Батьківська категорія",
            {
                "fields": ("parent_category", "new_parent_category"),
                "description": "Оберіть існуючу батьківську категорію або створіть нову",
            },
        ),
        ("Підкатегорія", {"fields": ("name",), "description": "Введіть назву підкатегорії"}),
    )

    # Override save to handle parent category from form
    def save_model(self, request, obj, form, change):
        # Set parent category from form data
        if "parent" in form.cleaned_data:
            obj.parent = form.cleaned_data["parent"]

        # New category without parent becomes a main category
        if not change and not obj.parent:
            obj.parent = None

        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        # Customize form for main categories
        form = super().get_form(request, obj, **kwargs)

        if obj and not obj.parent:
            form.base_fields["name"].label = "Назва категорії"
            form.base_fields["name"].help_text = "Введіть назву основної категорії"

        return form

    def get_queryset(self, request):
        # Optimize queries with prefetch_related
        qs = super().get_queryset(request)
        return qs.prefetch_related("children")


# Admin configuration for Transaction model
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("amount", "currency", "date", "table", "category_display", "description")
    list_filter = ("currency", "date", "table__user", "category__parent", "category")
    search_fields = ("description", "table__title", "category__name", "category__parent__name")
    date_hierarchy = "date"
    list_select_related = ("table", "category", "category__parent")
    autocomplete_fields = ["category"]

    def category_display(self, obj):
        # Display category hierarchy with clickable links
        if obj.category:
            url = reverse("admin:finances_category_change", args=[obj.category.id])
            if obj.category.parent:
                return format_html('<a href="{}">{} → {}</a>', url, obj.category.parent.name, obj.category.name)
            return format_html('<a href="{}">{}</a>', url, obj.category.name)
        return "—"

    category_display.short_description = "Категорія"
    category_display.admin_order_field = "category__name"

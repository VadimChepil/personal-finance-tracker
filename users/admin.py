from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'date_joined', 'last_login', 'is_staff', 'is_active')
    
    search_fields = ('email',)

    ordering = ('email', '-date_joined')
    
    list_filter = ('is_staff', 'is_active', 'date_joined')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(User, CustomUserAdmin)
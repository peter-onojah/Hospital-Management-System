from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Hospital Information', {'fields': ('role', 'phone', 'address', 'date_of_birth')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Hospital Information', {'fields': ('role', 'phone', 'address', 'date_of_birth')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
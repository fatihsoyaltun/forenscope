from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UnfoldModelAdmin, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Ek Bilgiler', {'fields': ('phone', 'department')}),
    )
    list_display = ['username', 'email', 'first_name', 'last_name', 'department', 'is_staff']

from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Plan", {"fields": ("tier", "is_premium")}),
    )
    list_display = ("username", "email", "tier", "is_premium", "is_staff")
    list_filter = UserAdmin.list_filter + ("tier", "is_premium")

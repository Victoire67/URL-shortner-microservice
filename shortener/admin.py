from .models import Url
from django.contrib import admin


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ("short_code", "original_url", "owner",
                    "is_active", "click_count", "created_at")

from .models import Url, Click, Tag
from django.contrib import admin


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ("short_code", "original_url", "owner",
                    "is_active", "click_count", "created_at")


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ("url", "clicked_at", "ip_address", "country", "city")
    list_filter = ("country", "clicked_at")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
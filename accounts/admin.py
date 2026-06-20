from django.contrib import admin
from .models import AccountProfile


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "phone", "is_phone_verified", "created_at")
    list_filter = ("is_phone_verified", "created_at")
    search_fields = ("user__username", "user__email", "full_name", "phone")

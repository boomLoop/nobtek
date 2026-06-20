from django.contrib import admin
from .models import FAQ, LeadMessage, SiteSetting, Testimonial


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ("هویت برند", {"fields": ("site_name", "tagline", "hero_title", "hero_subtitle", "meta_description")}),
        ("راه‌های ارتباطی", {"fields": ("contact_phone", "contact_email", "instagram_url", "whatsapp_url", "address")}),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("question", "answer")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("full_name", "role", "quote")


@admin.register(LeadMessage)
class LeadMessageAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email", "created_at", "is_checked")
    list_filter = ("is_checked", "created_at")
    search_fields = ("full_name", "phone", "email", "message")
    readonly_fields = ("created_at",)

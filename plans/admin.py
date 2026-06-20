from django.contrib import admin
from .models import PlanFeature, SubscriptionPlan, UserSubscription


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "monthly_price", "max_services", "max_bookings_per_month", "max_staff", "is_active", "is_featured", "order")
    list_editable = ("monthly_price", "is_active", "is_featured", "order")
    search_fields = ("name", "code", "description")
    inlines = [PlanFeatureInline]


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "starts_at", "ends_at", "is_active", "auto_renew")
    list_filter = ("plan", "is_active", "auto_renew")
    search_fields = ("user__username", "user__email")

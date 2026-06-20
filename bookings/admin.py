from django.contrib import admin
from .models import Booking, PaymentTransaction


class PaymentInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "customer_name", "customer_phone", "business", "service", "starts_at", "status", "is_paid", "payable_amount")
    list_filter = ("status", "is_paid", "starts_at", "business")
    search_fields = ("tracking_code", "customer_name", "customer_phone", "service__title", "business__title")
    readonly_fields = ("tracking_code", "created_at", "updated_at")
    inlines = [PaymentInline]
    actions = ["mark_confirmed", "mark_done", "mark_no_show"]

    @admin.action(description="تأیید رزروهای انتخاب‌شده")
    def mark_confirmed(self, request, queryset):
        queryset.update(status=Booking.STATUS_CONFIRMED)

    @admin.action(description="ثبت به عنوان انجام شده")
    def mark_done(self, request, queryset):
        queryset.update(status=Booking.STATUS_DONE)

    @admin.action(description="ثبت عدم حضور")
    def mark_no_show(self, request, queryset):
        queryset.update(status=Booking.STATUS_NO_SHOW)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount", "gateway", "status", "paid_at", "created_at")
    list_filter = ("status", "gateway", "created_at")
    search_fields = ("booking__tracking_code", "booking__customer_name", "authority")

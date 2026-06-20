from django.contrib import admin
from .models import BusinessCategory, BusinessProfile, Service, StaffMember, TimeBlock, WorkingHour


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0


class WorkingHourInline(admin.TabularInline):
    model = WorkingHour
    extra = 0


class StaffMemberInline(admin.TabularInline):
    model = StaffMember
    extra = 0


@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "order")
    list_editable = ("is_active", "order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "city", "is_verified", "is_published", "created_at")
    list_filter = ("category", "is_verified", "is_published", "created_at")
    search_fields = ("title", "owner__username", "phone", "city")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [StaffMemberInline, WorkingHourInline, ServiceInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "price", "duration_minutes", "capacity", "payment_mode", "is_active", "order")
    list_filter = ("payment_mode", "is_active", "business")
    list_editable = ("price", "duration_minutes", "capacity", "is_active", "order")
    search_fields = ("title", "business__title", "description")


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "business", "role", "phone", "is_active", "order")
    list_filter = ("is_active", "business")
    search_fields = ("full_name", "role", "phone", "business__title")


@admin.register(WorkingHour)
class WorkingHourAdmin(admin.ModelAdmin):
    list_display = ("business", "weekday", "opens_at", "closes_at", "is_open")
    list_filter = ("weekday", "is_open", "business")


@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "starts_at", "ends_at")
    list_filter = ("business", "starts_at")
    search_fields = ("title", "business__title")

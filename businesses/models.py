from datetime import datetime, timedelta, time

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class BusinessCategory(models.Model):
    name = models.CharField("نام دسته‌بندی", max_length=100, unique=True)
    slug = models.SlugField("اسلاگ", max_length=120, unique=True, allow_unicode=True)
    description = models.CharField("توضیح", max_length=220, blank=True)
    icon = models.CharField("آیکن", max_length=40, default="calendar-check")
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "دسته‌بندی کسب‌وکار"
        verbose_name_plural = "دسته‌بندی‌های کسب‌وکار"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class BusinessProfile(models.Model):
    TYPE_IN_PERSON = "in_person"
    TYPE_ONLINE = "online"
    TYPE_BOTH = "both"
    BUSINESS_TYPE_CHOICES = [
        (TYPE_IN_PERSON, "حضوری"),
        (TYPE_ONLINE, "آنلاین"),
        (TYPE_BOTH, "حضوری و آنلاین"),
    ]

    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business", verbose_name="مالک")
    category = models.ForeignKey(BusinessCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="businesses", verbose_name="دسته‌بندی")
    title = models.CharField("نام کسب‌وکار", max_length=140)
    slug = models.SlugField("لینک اختصاصی", max_length=160, unique=True, allow_unicode=True)
    short_description = models.CharField("توضیح کوتاه", max_length=240, blank=True)
    description = models.TextField("معرفی کامل", blank=True)
    business_type = models.CharField("نوع فعالیت", max_length=20, choices=BUSINESS_TYPE_CHOICES, default=TYPE_BOTH)
    city = models.CharField("شهر", max_length=80, blank=True)
    address = models.CharField("آدرس", max_length=260, blank=True)
    phone = models.CharField("شماره تماس", max_length=32, blank=True)
    instagram_url = models.URLField("اینستاگرام", blank=True)
    whatsapp_url = models.URLField("واتساپ", blank=True)
    website_url = models.URLField("وب‌سایت", blank=True)
    logo = models.ImageField("لوگو", upload_to="business/logos/", blank=True, null=True)
    cover = models.ImageField("کاور", upload_to="business/covers/", blank=True, null=True)
    booking_policy = models.TextField("قوانین رزرو", default="لطفاً در زمان انتخاب‌شده حضور داشته باشید. امکان لغو رزرو طبق قوانین کسب‌وکار انجام می‌شود.")
    cancellation_hours = models.PositiveIntegerField("امکان لغو تا چند ساعت قبل", default=24)
    is_verified = models.BooleanField("تأیید شده", default=False)
    is_published = models.BooleanField("منتشر شده", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "پروفایل کسب‌وکار"
        verbose_name_plural = "پروفایل‌های کسب‌وکار"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or f"business-{self.owner_id}"
            slug = base
            counter = 2
            while BusinessProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("businesses:public_profile", kwargs={"slug": self.slug})

    @property
    def active_services_count(self):
        return self.services.filter(is_active=True).count()


class StaffMember(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="staff_members", verbose_name="کسب‌وکار")
    full_name = models.CharField("نام کارمند", max_length=120)
    role = models.CharField("سمت", max_length=120, blank=True)
    phone = models.CharField("شماره تماس", max_length=32, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "کارمند"
        verbose_name_plural = "کارمندان"
        ordering = ["order", "full_name"]

    def __str__(self):
        return self.full_name


class Service(models.Model):
    PAYMENT_NONE = "none"
    PAYMENT_FULL = "full"
    PAYMENT_FIXED_DEPOSIT = "fixed_deposit"
    PAYMENT_PERCENT_DEPOSIT = "percent_deposit"
    PAYMENT_CHOICES = [
        (PAYMENT_NONE, "بدون پرداخت"),
        (PAYMENT_FULL, "پرداخت کامل"),
        (PAYMENT_FIXED_DEPOSIT, "بیعانه ثابت"),
        (PAYMENT_PERCENT_DEPOSIT, "بیعانه درصدی"),
    ]

    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="services", verbose_name="کسب‌وکار")
    staff = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, blank=True, related_name="services", verbose_name="ارائه‌دهنده")
    title = models.CharField("نام خدمت", max_length=140)
    description = models.TextField("توضیح خدمت", blank=True)
    price = models.PositiveIntegerField("قیمت به تومان", default=0)
    duration_minutes = models.PositiveIntegerField("مدت‌زمان به دقیقه", default=60)
    buffer_minutes = models.PositiveIntegerField("فاصله بعد از رزرو", default=0)
    capacity = models.PositiveIntegerField("ظرفیت هر بازه", default=1)
    payment_mode = models.CharField("نوع پرداخت", max_length=24, choices=PAYMENT_CHOICES, default=PAYMENT_NONE)
    deposit_amount = models.PositiveIntegerField("مبلغ بیعانه ثابت", default=0)
    deposit_percent = models.PositiveIntegerField("درصد بیعانه", default=0)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "خدمت قابل رزرو"
        verbose_name_plural = "خدمات قابل رزرو"
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    @property
    def total_block_minutes(self):
        return self.duration_minutes + self.buffer_minutes

    @property
    def required_payment_amount(self):
        if self.payment_mode == self.PAYMENT_FULL:
            return self.price
        if self.payment_mode == self.PAYMENT_FIXED_DEPOSIT:
            return self.deposit_amount
        if self.payment_mode == self.PAYMENT_PERCENT_DEPOSIT:
            return int(self.price * min(self.deposit_percent, 100) / 100)
        return 0

    @property
    def needs_payment(self):
        return self.required_payment_amount > 0


class WorkingHour(models.Model):
    SATURDAY = 5
    SUNDAY = 6
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    WEEKDAY_CHOICES = [
        (SATURDAY, "شنبه"),
        (SUNDAY, "یکشنبه"),
        (MONDAY, "دوشنبه"),
        (TUESDAY, "سه‌شنبه"),
        (WEDNESDAY, "چهارشنبه"),
        (THURSDAY, "پنجشنبه"),
        (FRIDAY, "جمعه"),
    ]

    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="working_hours", verbose_name="کسب‌وکار")
    weekday = models.PositiveSmallIntegerField("روز هفته", choices=WEEKDAY_CHOICES)
    opens_at = models.TimeField("شروع کار", default=time(9, 0))
    closes_at = models.TimeField("پایان کار", default=time(18, 0))
    break_starts_at = models.TimeField("شروع استراحت", blank=True, null=True)
    break_ends_at = models.TimeField("پایان استراحت", blank=True, null=True)
    is_open = models.BooleanField("باز است", default=True)

    class Meta:
        verbose_name = "ساعت کاری"
        verbose_name_plural = "ساعت‌های کاری"
        unique_together = ("business", "weekday")
        ordering = ["weekday"]

    def __str__(self):
        return f"{self.business} - {self.get_weekday_display()}"


class TimeBlock(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="time_blocks", verbose_name="کسب‌وکار")
    title = models.CharField("عنوان", max_length=120, default="زمان بسته")
    starts_at = models.DateTimeField("شروع")
    ends_at = models.DateTimeField("پایان")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "بستن زمان"
        verbose_name_plural = "زمان‌های بسته شده"
        ordering = ["-starts_at"]

    def __str__(self):
        return f"{self.title} - {self.business}"


# Backward-compatible public API. The implementation lives in businesses.availability
# so it can be tested and extended without bloating model definitions.
def get_available_slots(service: Service, days: int = 10):
    from .availability import get_available_slots as _get_available_slots

    return _get_available_slots(service, days=days)

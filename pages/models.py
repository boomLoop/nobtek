from django.db import models


class SiteSetting(models.Model):
    site_name = models.CharField("نام سایت", max_length=80, default="نوبتک")
    tagline = models.CharField("شعار", max_length=180, default="لینک رزرو آنلاین برای هر کسب‌وکار")
    hero_title = models.CharField("تیتر اصلی", max_length=220, default="برای کسب‌وکارت صفحه رزرو آنلاین بساز")
    hero_subtitle = models.TextField("زیرتیتر اصلی", default="مشتری‌ها ۲۴ ساعته وقت، خدمت، کلاس یا مکان رزرو می‌کنند و تو همه چیز را از یک پنل حرفه‌ای مدیریت می‌کنی.")
    contact_phone = models.CharField("شماره تماس", max_length=32, blank=True)
    contact_email = models.EmailField("ایمیل تماس", blank=True)
    instagram_url = models.URLField("لینک اینستاگرام", blank=True)
    whatsapp_url = models.URLField("لینک واتساپ", blank=True)
    address = models.CharField("آدرس", max_length=260, blank=True)
    meta_description = models.CharField("متا دیسکریپشن", max_length=260, default="نوبتک پلتفرم ساخت صفحه رزرو آنلاین برای کسب‌وکارها، مشاوران، کلاس‌ها، سالن‌ها و مکان‌های قابل رزرو است.")
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.site_name


class FAQ(models.Model):
    question = models.CharField("سوال", max_length=220)
    answer = models.TextField("پاسخ")
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "سوال پرتکرار"
        verbose_name_plural = "سوالات پرتکرار"
        ordering = ["order", "id"]

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    full_name = models.CharField("نام", max_length=120)
    role = models.CharField("سمت / کسب‌وکار", max_length=160, blank=True)
    quote = models.TextField("متن نظر")
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "نظر مشتری"
        verbose_name_plural = "نظرات مشتریان"
        ordering = ["order", "id"]

    def __str__(self):
        return self.full_name


class LeadMessage(models.Model):
    full_name = models.CharField("نام و نام خانوادگی", max_length=120)
    phone = models.CharField("شماره موبایل", max_length=32)
    email = models.EmailField("ایمیل", blank=True)
    message = models.TextField("پیام")
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    is_checked = models.BooleanField("بررسی شده", default=False)

    class Meta:
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.phone}"

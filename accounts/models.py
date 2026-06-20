from django.conf import settings
from django.db import models


class AccountProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile", verbose_name="کاربر")
    phone = models.CharField("شماره موبایل", max_length=32, blank=True)
    full_name = models.CharField("نام کامل", max_length=120, blank=True)
    is_phone_verified = models.BooleanField("موبایل تأیید شده", default=False)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "پروفایل کاربر"
        verbose_name_plural = "پروفایل کاربران"

    def __str__(self):
        return self.full_name or self.user.username

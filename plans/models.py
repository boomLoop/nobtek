from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta


class SubscriptionPlan(models.Model):
    PLAN_FREE = "free"
    PLAN_SILVER = "silver"
    PLAN_GOLD = "gold"
    PLAN_ENTERPRISE = "enterprise"
    PLAN_CHOICES = [
        (PLAN_FREE, "رایگان"),
        (PLAN_SILVER, "نقره‌ای"),
        (PLAN_GOLD, "طلایی"),
        (PLAN_ENTERPRISE, "سازمانی"),
    ]

    name = models.CharField("نام پلن", max_length=80)
    code = models.SlugField("کد پلن", max_length=32, unique=True, choices=PLAN_CHOICES)
    monthly_price = models.PositiveIntegerField("قیمت ماهانه به تومان", default=0)
    yearly_price = models.PositiveIntegerField("قیمت سالانه به تومان", default=0)
    max_services = models.PositiveIntegerField("حداکثر خدمات", default=3)
    max_bookings_per_month = models.PositiveIntegerField("حداکثر رزرو ماهانه", default=30)
    max_staff = models.PositiveIntegerField("حداکثر کارمند", default=1)
    sms_credit = models.PositiveIntegerField("اعتبار پیامک ماهانه", default=0)
    online_payment = models.BooleanField("پرداخت آنلاین", default=False)
    deposit_payment = models.BooleanField("بیعانه", default=False)
    remove_branding = models.BooleanField("حذف برندینگ", default=False)
    custom_domain = models.BooleanField("دامنه اختصاصی", default=False)
    advanced_reports = models.BooleanField("گزارش پیشرفته", default=False)
    is_active = models.BooleanField("فعال", default=True)
    is_featured = models.BooleanField("پلن پیشنهادی", default=False)
    order = models.PositiveIntegerField("ترتیب", default=0)
    description = models.CharField("توضیح کوتاه", max_length=220, blank=True)

    class Meta:
        verbose_name = "پلن اشتراک"
        verbose_name_plural = "پلن‌های اشتراک"
        ordering = ["order", "monthly_price"]

    def __str__(self):
        return self.name


class PlanFeature(models.Model):
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name="features", verbose_name="پلن")
    title = models.CharField("عنوان قابلیت", max_length=160)
    is_available = models.BooleanField("فعال برای این پلن", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "قابلیت پلن"
        verbose_name_plural = "قابلیت‌های پلن‌ها"
        ordering = ["plan", "order", "id"]

    def __str__(self):
        return f"{self.plan.name}: {self.title}"


class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription", verbose_name="کاربر")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions", verbose_name="پلن")
    starts_at = models.DateTimeField("شروع", default=timezone.now)
    ends_at = models.DateTimeField("پایان", blank=True, null=True)
    is_active = models.BooleanField("فعال", default=True)
    auto_renew = models.BooleanField("تمدید خودکار", default=False)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "اشتراک کاربر"
        verbose_name_plural = "اشتراک‌های کاربران"

    def __str__(self):
        return f"{self.user} - {self.plan}"

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.ends_at and self.ends_at < timezone.now():
            return False
        return True

    @classmethod
    def create_default_for(cls, user):
        plan = SubscriptionPlan.objects.filter(code=SubscriptionPlan.PLAN_FREE, is_active=True).first()
        if not plan:
            plan = SubscriptionPlan.objects.create(name="رایگان", code=SubscriptionPlan.PLAN_FREE)
        return cls.objects.create(user=user, plan=plan, starts_at=timezone.now(), ends_at=timezone.now() + timedelta(days=3650))

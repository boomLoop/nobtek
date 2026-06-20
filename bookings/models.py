from django.db import models
from django.utils import timezone


class Booking(models.Model):
    STATUS_PENDING = "pending"
    STATUS_AWAITING_PAYMENT = "awaiting_payment"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED_BY_CUSTOMER = "cancelled_by_customer"
    STATUS_CANCELLED_BY_BUSINESS = "cancelled_by_business"
    STATUS_DONE = "done"
    STATUS_NO_SHOW = "no_show"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار تأیید"),
        (STATUS_AWAITING_PAYMENT, "در انتظار پرداخت"),
        (STATUS_CONFIRMED, "تأیید شده"),
        (STATUS_CANCELLED_BY_CUSTOMER, "لغو شده توسط مشتری"),
        (STATUS_CANCELLED_BY_BUSINESS, "لغو شده توسط کسب‌وکار"),
        (STATUS_DONE, "انجام شده"),
        (STATUS_NO_SHOW, "عدم حضور"),
        (STATUS_EXPIRED, "منقضی شده"),
    ]

    business = models.ForeignKey("businesses.BusinessProfile", on_delete=models.CASCADE, related_name="bookings", verbose_name="کسب‌وکار")
    service = models.ForeignKey("businesses.Service", on_delete=models.PROTECT, related_name="bookings", verbose_name="خدمت")
    staff = models.ForeignKey("businesses.StaffMember", on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings", verbose_name="ارائه‌دهنده")
    customer_name = models.CharField("نام مشتری", max_length=120)
    customer_phone = models.CharField("شماره موبایل", max_length=32)
    customer_email = models.EmailField("ایمیل", blank=True)
    notes = models.TextField("توضیحات", blank=True)
    starts_at = models.DateTimeField("شروع رزرو")
    ends_at = models.DateTimeField("پایان رزرو")
    status = models.CharField("وضعیت", max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    price = models.PositiveIntegerField("قیمت خدمت", default=0)
    payable_amount = models.PositiveIntegerField("مبلغ قابل پرداخت", default=0)
    is_paid = models.BooleanField("پرداخت شده", default=False)
    tracking_code = models.CharField("کد پیگیری", max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "رزرو"
        verbose_name_plural = "رزروها"
        ordering = ["-starts_at"]
        indexes = [
            models.Index(fields=["business", "starts_at"]),
            models.Index(fields=["service", "starts_at"]),
            models.Index(fields=["tracking_code"]),
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.service}"

    @classmethod
    def occupying_statuses(cls):
        return [cls.STATUS_PENDING, cls.STATUS_CONFIRMED, cls.STATUS_AWAITING_PAYMENT]

    @classmethod
    def cancellable_statuses(cls):
        return {cls.STATUS_PENDING, cls.STATUS_CONFIRMED, cls.STATUS_AWAITING_PAYMENT}

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            base = timezone.now().strftime("NB%y%m%d%H%M%S")
            code = base
            counter = 1
            while Booking.objects.filter(tracking_code=code).exclude(pk=self.pk).exists():
                code = f"{base}{counter}"
                counter += 1
            self.tracking_code = code
        if self._state.adding:
            if not self.price:
                self.price = self.service.price
            self.payable_amount = self.service.required_payment_amount
        elif not self.payable_amount and self.service.needs_payment:
            self.payable_amount = self.service.required_payment_amount
        super().save(*args, **kwargs)

    @property
    def can_be_cancelled_by_customer(self):
        limit = timezone.now() + timezone.timedelta(hours=self.business.cancellation_hours)
        return self.starts_at > limit and self.status in self.cancellable_statuses()


class PaymentTransaction(models.Model):
    STATUS_INIT = "init"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [
        (STATUS_INIT, "ایجاد شده"),
        (STATUS_SUCCESS, "موفق"),
        (STATUS_FAILED, "ناموفق"),
        (STATUS_REFUNDED, "برگشت داده شده"),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments", verbose_name="رزرو")
    amount = models.PositiveIntegerField("مبلغ", default=0)
    gateway = models.CharField("درگاه", max_length=80, default="درگاه آزمایشی")
    authority = models.CharField("شناسه پرداخت", max_length=120, blank=True)
    status = models.CharField("وضعیت", max_length=16, choices=STATUS_CHOICES, default=STATUS_INIT)
    paid_at = models.DateTimeField("زمان پرداخت", blank=True, null=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "تراکنش پرداخت"
        verbose_name_plural = "تراکنش‌های پرداخت"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.booking.tracking_code} - {self.amount}"

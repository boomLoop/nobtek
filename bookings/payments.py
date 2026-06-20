from dataclasses import dataclass

from django.conf import settings
from django.urls import reverse


@dataclass(frozen=True)
class PaymentRequest:
    ok: bool
    redirect_url: str = ""
    message: str = ""


class PaymentGatewayError(Exception):
    pass


class DemoGateway:
    code = "demo"
    title = "درگاه آزمایشی نوبتک"

    def create_payment(self, request, booking) -> PaymentRequest:
        return PaymentRequest(
            ok=True,
            redirect_url=reverse("bookings:pay_demo", kwargs={"tracking_code": booking.tracking_code}),
            message="پرداخت آزمایشی آماده است.",
        )


def get_gateway():
    provider = getattr(settings, "NOBTEK_PAYMENT_GATEWAY", "demo")
    if provider == "demo":
        return DemoGateway()
    raise PaymentGatewayError("درگاه پرداخت انتخاب‌شده هنوز در تنظیمات پروژه پیاده‌سازی نشده است.")

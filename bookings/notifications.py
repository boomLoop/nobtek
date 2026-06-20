import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _sms_console(phone: str, message: str) -> bool:
    logger.info("SMS console backend | to=%s | message=%s", phone, message)
    return True


def send_sms(phone: str, message: str) -> bool:
    """SMS adapter placeholder.

    Set NOBTEK_SMS_BACKEND=console for development. For production, plug Kavenegar,
    sms.ir, or any provider here without touching views/business logic.
    """
    backend = getattr(settings, "NOBTEK_SMS_BACKEND", "console")
    if backend == "console":
        return _sms_console(phone, message)
    logger.warning("Unknown SMS backend %s; SMS was not sent.", backend)
    return False


def send_booking_created_notifications(booking) -> None:
    message = (
        f"رزرو شما در نوبتک ثبت شد. کد پیگیری: {booking.tracking_code}. "
        f"وضعیت: {booking.get_status_display()}"
    )
    send_sms(booking.customer_phone, message)
    owner_phone = getattr(getattr(booking.business.owner, "profile", None), "phone", "") or booking.business.phone
    if owner_phone:
        send_sms(owner_phone, f"رزرو جدید برای {booking.service.title}: {booking.customer_name} - {booking.tracking_code}")
    if booking.customer_email:
        try:
            send_mail(
                subject=f"کد پیگیری رزرو {booking.tracking_code}",
                message=message,
                from_email=None,
                recipient_list=[booking.customer_email],
                fail_silently=True,
            )
        except Exception:  # noqa: BLE001 - notification must never break booking flow
            logger.exception("Booking email notification failed for %s", booking.tracking_code)


def send_booking_status_notification(booking) -> None:
    send_sms(booking.customer_phone, f"وضعیت رزرو {booking.tracking_code}: {booking.get_status_display()}")

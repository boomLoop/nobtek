from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from businesses.availability import is_slot_available
from businesses.models import Service, StaffMember
from .models import Booking, PaymentTransaction
from .notifications import send_booking_created_notifications, send_booking_status_notification


class BookingError(Exception):
    pass


def _lock_service_and_staff(service_id: int) -> Service:
    service = Service.objects.select_for_update().select_related("business", "staff", "business__owner").get(pk=service_id)
    if service.staff_id:
        StaffMember.objects.select_for_update().filter(pk=service.staff_id).first()
    return service


def owner_monthly_booking_limit_reached(business, starts_at) -> bool:
    subscription = getattr(business.owner, "subscription", None)
    if not subscription or not subscription.is_valid or not subscription.plan:
        return False
    plan = subscription.plan
    if not plan.max_bookings_per_month:
        return False
    local_start = timezone.localtime(starts_at).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if local_start.month == 12:
        local_end = local_start.replace(year=local_start.year + 1, month=1)
    else:
        local_end = local_start.replace(month=local_start.month + 1)
    used = business.bookings.filter(
        created_at__gte=local_start,
        created_at__lt=local_end,
    ).exclude(
        status__in=[Booking.STATUS_CANCELLED_BY_CUSTOMER, Booking.STATUS_CANCELLED_BY_BUSINESS, Booking.STATUS_EXPIRED]
    ).count()
    return used >= plan.max_bookings_per_month


def create_public_booking(*, service_id: int, business_id: int, selected_start, cleaned_data) -> Booking:
    with transaction.atomic():
        service = _lock_service_and_staff(service_id)
        if service.business_id != business_id or not service.is_active or not service.business.is_published:
            raise BookingError("خدمت انتخاب‌شده معتبر نیست.")

        selected_start = timezone.localtime(selected_start).replace(second=0, microsecond=0)
        result = is_slot_available(service, selected_start)
        if not result.ok:
            raise BookingError(result.reason or "این زمان دیگر آزاد نیست.")

        if owner_monthly_booking_limit_reached(service.business, selected_start):
            raise BookingError("ظرفیت رزرو ماهانه این کسب‌وکار در پلن فعلی تکمیل شده است.")

        booking = Booking.objects.create(
            business=service.business,
            service=service,
            staff=service.staff,
            customer_name=cleaned_data["customer_name"],
            customer_phone=cleaned_data["customer_phone"],
            customer_email=cleaned_data.get("customer_email", ""),
            notes=cleaned_data.get("notes", ""),
            starts_at=selected_start,
            ends_at=selected_start + timedelta(minutes=service.duration_minutes),
            status=Booking.STATUS_AWAITING_PAYMENT if service.needs_payment else Booking.STATUS_PENDING,
            price=service.price,
            is_paid=False,
        )
        if service.needs_payment:
            PaymentTransaction.objects.create(
                booking=booking,
                amount=service.required_payment_amount,
                gateway="درگاه آزمایشی نوبتک",
                status=PaymentTransaction.STATUS_INIT,
            )

    send_booking_created_notifications(booking)
    return booking


def confirm_demo_payment(booking: Booking) -> Booking:
    if not booking.service.needs_payment:
        return booking
    with transaction.atomic():
        booking = Booking.objects.select_for_update().select_related("service", "business").get(pk=booking.pk)
        if booking.status != Booking.STATUS_AWAITING_PAYMENT:
            return booking
        payment = booking.payments.select_for_update().order_by("-created_at").first()
        if payment:
            payment.status = PaymentTransaction.STATUS_SUCCESS
            payment.paid_at = timezone.now()
            payment.authority = f"DEMO-{booking.tracking_code}-{int(timezone.now().timestamp())}"
            payment.save(update_fields=["status", "paid_at", "authority"])
        booking.is_paid = True
        booking.status = Booking.STATUS_CONFIRMED
        booking.save(update_fields=["is_paid", "status", "updated_at"])
    send_booking_status_notification(booking)
    return booking


def cancel_booking_by_customer(booking: Booking) -> Booking:
    with transaction.atomic():
        booking = Booking.objects.select_for_update().select_related("business", "service").get(pk=booking.pk)
        if not booking.can_be_cancelled_by_customer:
            raise BookingError("امکان لغو این رزرو طبق قوانین کسب‌وکار وجود ندارد.")
        booking.status = Booking.STATUS_CANCELLED_BY_CUSTOMER
        booking.save(update_fields=["status", "updated_at"])
    send_booking_status_notification(booking)
    return booking

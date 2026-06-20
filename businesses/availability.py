from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Service


@dataclass(frozen=True)
class AvailabilityResult:
    ok: bool
    reason: str = ""


def _overlaps(start_a, end_a, start_b, end_b) -> bool:
    return start_a < end_b and end_a > start_b


def _aware(dt):
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return timezone.localtime(dt)


def _booking_block_end(booking) -> datetime:
    service = getattr(booking, "service", None)
    buffer_minutes = getattr(service, "buffer_minutes", 0) or 0
    return booking.ends_at + timedelta(minutes=buffer_minutes)


def _candidate_bounds(service: Service, start: datetime):
    start = _aware(start).replace(second=0, microsecond=0)
    appointment_end = start + timedelta(minutes=service.duration_minutes)
    blocked_end = start + timedelta(minutes=service.total_block_minutes)
    return start, appointment_end, blocked_end


def is_slot_available(service: Service, start: datetime, *, now=None) -> AvailabilityResult:
    """Validate one slot using business hours, breaks, blocks, staff conflicts and service capacity.

    The appointment itself must finish inside working hours. The service buffer is also
    considered busy time for collision checks so the next customer cannot be placed too close.
    """
    from bookings.models import Booking

    now = timezone.localtime(now or timezone.now())
    start, appointment_end, blocked_end = _candidate_bounds(service, start)
    business = service.business

    if start <= now + timedelta(minutes=30):
        return AvailabilityResult(False, "این زمان بیش از حد نزدیک است یا گذشته است.")

    working = business.working_hours.filter(weekday=start.weekday(), is_open=True).first()
    if not working:
        return AvailabilityResult(False, "کسب‌وکار در این روز باز نیست.")

    day = start.date()
    opens_at = _aware(datetime.combine(day, working.opens_at))
    closes_at = _aware(datetime.combine(day, working.closes_at))
    if start < opens_at or appointment_end > closes_at:
        return AvailabilityResult(False, "این زمان خارج از ساعت کاری است.")

    if working.break_starts_at and working.break_ends_at:
        break_start = _aware(datetime.combine(day, working.break_starts_at))
        break_end = _aware(datetime.combine(day, working.break_ends_at))
        if _overlaps(start, appointment_end, break_start, break_end):
            return AvailabilityResult(False, "این زمان با زمان استراحت تداخل دارد.")

    if business.time_blocks.filter(starts_at__lt=blocked_end, ends_at__gt=start).exists():
        return AvailabilityResult(False, "این زمان توسط کسب‌وکار بسته شده است.")

    occupying_statuses = Booking.occupying_statuses()
    qs = (
        Booking.objects.select_related("service", "staff")
        .filter(business=business, status__in=occupying_statuses)
        .filter(starts_at__date=day)
    )

    same_service_overlaps = 0
    staff_conflict = False
    for booking in qs:
        existing_start = timezone.localtime(booking.starts_at)
        existing_end = timezone.localtime(_booking_block_end(booking))
        if not _overlaps(start, blocked_end, existing_start, existing_end):
            continue
        if booking.service_id == service.id:
            same_service_overlaps += 1
        if service.staff_id and booking.staff_id == service.staff_id:
            staff_conflict = True

    if staff_conflict:
        return AvailabilityResult(False, "ارائه‌دهنده این خدمت در این زمان رزرو دیگری دارد.")
    if same_service_overlaps >= service.capacity:
        return AvailabilityResult(False, "ظرفیت این زمان تکمیل شده است.")

    return AvailabilityResult(True)


def get_available_slots(service: Service, days: int = 10, *, now=None, slot_step: int = 15):
    business = service.business
    now = timezone.localtime(now or timezone.now())
    today = now.date()
    slots = []

    for offset in range(days):
        current_date = today + timedelta(days=offset)
        working = business.working_hours.filter(weekday=current_date.weekday(), is_open=True).first()
        if not working:
            continue

        start_dt = _aware(datetime.combine(current_date, working.opens_at))
        end_dt = _aware(datetime.combine(current_date, working.closes_at))
        candidate = start_dt.replace(second=0, microsecond=0)

        while candidate + timedelta(minutes=service.duration_minutes) <= end_dt:
            result = is_slot_available(service, candidate, now=now)
            if result.ok:
                slots.append({
                    "start": candidate,
                    "end": candidate + timedelta(minutes=service.duration_minutes),
                    "block_end": candidate + timedelta(minutes=service.total_block_minutes),
                })
            candidate += timedelta(minutes=slot_step)

    return slots

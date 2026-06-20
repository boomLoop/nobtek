from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from businesses.models import BusinessProfile, Service, get_available_slots
from businesses.persian_datetime import fa_number, persian_date_full, persian_date_short, persian_time, persian_weekday
from .forms import PublicBookingForm
from .models import Booking
from .services import BookingError, cancel_booking_by_customer, confirm_demo_payment, create_public_booking
from .tokens import make_cancel_token, validate_cancel_token


def _slot_period_title(hour: int) -> str:
    if hour < 12:
        return "صبح"
    if hour < 17:
        return "ظهر و عصر"
    return "عصر و شب"


def _prepare_slot_days(slots):
    """Group available slots by Persian day and compact time periods for the booking UI."""
    grouped = []
    day_index = {}
    period_order = ["صبح", "ظهر و عصر", "عصر و شب"]

    for slot in slots:
        start = timezone.localtime(slot["start"])
        end = timezone.localtime(slot["end"])
        day_key = start.date().isoformat()
        if day_key not in day_index:
            day = {
                "key": day_key,
                "weekday": persian_weekday(start),
                "short_date": persian_date_short(start),
                "full_date": persian_date_full(start),
                "count": 0,
                "periods_map": {title: [] for title in period_order},
            }
            day_index[day_key] = day
            grouped.append(day)

        title = _slot_period_title(start.hour)
        day_index[day_key]["periods_map"][title].append({
            "value": slot["start"].isoformat(),
            "start_time": persian_time(start),
            "end_time": persian_time(end),
            "iso_date": day_key,
        })
        day_index[day_key]["count"] += 1

    for day in grouped:
        day["count_label"] = fa_number(day["count"])
        day["periods"] = [
            {"title": title, "slots": day["periods_map"][title]}
            for title in period_order
            if day["periods_map"][title]
        ]
        del day["periods_map"]

    return grouped


def _parse_selected_slot(value):
    selected = parse_datetime(value or "")
    if selected is None:
        return None
    if timezone.is_naive(selected):
        selected = timezone.make_aware(selected)
    return timezone.localtime(selected).replace(second=0, microsecond=0)


def create_booking(request, business_slug, service_id):
    business = get_object_or_404(BusinessProfile, slug=business_slug, is_published=True)
    service = get_object_or_404(Service.objects.select_related("staff", "business"), pk=service_id, business=business, is_active=True)
    slots = get_available_slots(service, days=14)

    if request.method == "POST":
        form = PublicBookingForm(request.POST, slots=slots)
        if form.is_valid():
            selected = _parse_selected_slot(form.cleaned_data["slot"])
            if selected is None:
                messages.error(request, "زمان انتخاب‌شده معتبر نیست.")
                return redirect("bookings:create", business_slug=business.slug, service_id=service.id)
            try:
                booking = create_public_booking(
                    service_id=service.id,
                    business_id=business.id,
                    selected_start=selected,
                    cleaned_data=form.cleaned_data,
                )
            except BookingError as exc:
                messages.error(request, str(exc))
                return redirect("bookings:create", business_slug=business.slug, service_id=service.id)
            messages.success(request, "رزرو شما با موفقیت ثبت شد.")
            return redirect("bookings:detail", tracking_code=booking.tracking_code)
    else:
        form = PublicBookingForm(slots=slots)

    slot_days = _prepare_slot_days(slots)
    selected_slot = request.POST.get("slot", "") if request.method == "POST" else ""
    selected_day_key = ""
    if selected_slot:
        for day in slot_days:
            if any(item["value"] == selected_slot for period in day["periods"] for item in period["slots"]):
                selected_day_key = day["key"]
                break
    if not selected_day_key and slot_days:
        selected_day_key = slot_days[0]["key"]

    return render(request, "bookings/create_booking.html", {
        "business": business,
        "service": service,
        "form": form,
        "slots": slots,
        "slot_days": slot_days,
        "selected_slot": selected_slot,
        "selected_day_key": selected_day_key,
        "meta_title": f"رزرو {service.title} - {business.title}",
        "meta_description": f"رزرو آنلاین {service.title} در {business.title}. انتخاب زمان آزاد با تقویم فارسی و ثبت سریع نوبت در نوبتک.",
    })


def booking_detail(request, tracking_code):
    booking = get_object_or_404(Booking.objects.select_related("business", "service", "staff"), tracking_code=tracking_code)
    return render(request, "bookings/booking_detail.html", {
        "booking": booking,
        "cancel_token": make_cancel_token(booking),
        "meta_title": f"کد پیگیری رزرو {booking.tracking_code}",
        "meta_robots": "noindex, nofollow",
    })


@require_POST
def demo_payment_success(request, tracking_code):
    booking = get_object_or_404(Booking.objects.select_related("service", "business"), tracking_code=tracking_code)
    if not booking.service.needs_payment:
        return redirect("bookings:detail", tracking_code=tracking_code)
    booking = confirm_demo_payment(booking)
    messages.success(request, "پرداخت آزمایشی با موفقیت ثبت شد و رزرو شما قطعی شد.")
    return redirect("bookings:detail", tracking_code=booking.tracking_code)


@require_POST
def cancel_booking(request, tracking_code):
    booking = get_object_or_404(Booking.objects.select_related("business", "service"), tracking_code=tracking_code)
    token = request.POST.get("token", "")
    if not validate_cancel_token(booking, token):
        messages.error(request, "درخواست لغو معتبر نیست. لطفاً از همان صفحه پیگیری رزرو اقدام کنید.")
        return redirect("bookings:detail", tracking_code=tracking_code)
    try:
        cancel_booking_by_customer(booking)
        messages.success(request, "رزرو شما لغو شد.")
    except BookingError as exc:
        messages.error(request, str(exc))
    return redirect("bookings:detail", tracking_code=tracking_code)

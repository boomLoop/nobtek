from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_time

from bookings.forms import BookingStatusForm
from bookings.models import Booking
from bookings.notifications import send_booking_status_notification
from businesses.forms import BusinessProfileForm, ServiceForm, StaffMemberForm, TimeBlockForm, WorkingHourForm
from businesses.models import BusinessProfile, Service, StaffMember, TimeBlock, WorkingHour
from plans.models import SubscriptionPlan
from .forms import BusinessRegistrationForm, PersianAuthenticationForm


class NobtekLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = PersianAuthenticationForm
    redirect_authenticated_user = True


class NobtekLogoutView(LogoutView):
    next_page = reverse_lazy("pages:home")


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = BusinessRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "ثبت‌نام انجام شد. صفحه رزرو شما آماده است.")
            return redirect("accounts:dashboard")
    else:
        form = BusinessRegistrationForm()
    return render(request, "accounts/register.html", {"form": form, "meta_title": "ساخت صفحه رزرو رایگان در نوبتک"})


def _owner_business(user):
    return getattr(user, "business", None)


def _current_plan(user):
    subscription = getattr(user, "subscription", None)
    if subscription and subscription.is_valid:
        return subscription.plan
    return None


@login_required
def dashboard(request):
    business = _owner_business(request.user)
    if not business:
        messages.warning(request, "برای استفاده از داشبورد ابتدا کسب‌وکار خود را ثبت کنید.")
        return redirect("pages:home")

    now = timezone.now()
    today_start = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)
    month_start = today_start.replace(day=1)
    bookings = business.bookings.all()
    active_statuses = Booking.occupying_statuses()
    stats = {
        "today": bookings.filter(starts_at__gte=today_start, starts_at__lt=today_end).count(),
        "upcoming": bookings.filter(starts_at__gte=now, status__in=active_statuses).count(),
        "pending": bookings.filter(status=Booking.STATUS_PENDING).count(),
        "month_income": bookings.filter(is_paid=True, created_at__gte=month_start).aggregate(total=Sum("payable_amount"))["total"] or 0,
        "month_bookings": bookings.filter(created_at__gte=month_start).exclude(status__in=[Booking.STATUS_CANCELLED_BY_CUSTOMER, Booking.STATUS_CANCELLED_BY_BUSINESS, Booking.STATUS_EXPIRED]).count(),
    }
    plan = _current_plan(request.user)
    recent_bookings = bookings.select_related("service", "staff").order_by("-created_at")[:8]
    upcoming_bookings = bookings.filter(starts_at__gte=now, status__in=active_statuses).select_related("service", "staff").order_by("starts_at")[:6]
    return render(request, "accounts/dashboard.html", {
        "business": business,
        "stats": stats,
        "recent_bookings": recent_bookings,
        "upcoming_bookings": upcoming_bookings,
        "plan": plan,
    })


@login_required
def business_settings(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    if request.method == "POST":
        form = BusinessProfileForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, "تنظیمات صفحه کسب‌وکار ذخیره شد.")
            return redirect("accounts:business_settings")
    else:
        form = BusinessProfileForm(instance=business)
    return render(request, "accounts/business_settings.html", {"form": form, "business": business})


@login_required
def staff_list(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    staff_members = business.staff_members.all()
    plan = _current_plan(request.user)
    return render(request, "accounts/staff_list.html", {"business": business, "staff_members": staff_members, "plan": plan})


@login_required
def staff_create(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    plan = _current_plan(request.user)
    if plan and business.staff_members.count() >= plan.max_staff:
        messages.error(request, "به محدودیت تعداد کارمند در پلن فعلی رسیده‌اید.")
        return redirect("accounts:staff")
    if request.method == "POST":
        form = StaffMemberForm(request.POST)
        if form.is_valid():
            staff = form.save(commit=False)
            staff.business = business
            staff.save()
            messages.success(request, "کارمند/ارائه‌دهنده جدید ثبت شد.")
            return redirect("accounts:staff")
    else:
        form = StaffMemberForm()
    return render(request, "accounts/staff_form.html", {"business": business, "form": form, "title": "افزودن کارمند"})


@login_required
def staff_update(request, pk):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    staff = get_object_or_404(StaffMember, pk=pk, business=business)
    if request.method == "POST":
        form = StaffMemberForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات کارمند بروزرسانی شد.")
            return redirect("accounts:staff")
    else:
        form = StaffMemberForm(instance=staff)
    return render(request, "accounts/staff_form.html", {"business": business, "form": form, "title": "ویرایش کارمند"})


@login_required
def service_list(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    services = business.services.select_related("staff").all()
    plan = _current_plan(request.user)
    return render(request, "accounts/service_list.html", {"business": business, "services": services, "plan": plan})


@login_required
def service_create(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    plan = _current_plan(request.user)
    if plan and business.services.count() >= plan.max_services:
        messages.error(request, "به محدودیت تعداد خدمات در پلن فعلی رسیده‌اید. برای افزودن خدمات بیشتر، پنل را ارتقا دهید.")
        return redirect("accounts:services")

    if request.method == "POST":
        form = ServiceForm(request.POST, business=business, plan=plan)
        if form.is_valid():
            service = form.save(commit=False)
            service.business = business
            service.save()
            messages.success(request, "خدمت جدید ثبت شد.")
            return redirect("accounts:services")
    else:
        form = ServiceForm(business=business, plan=plan)
    return render(request, "accounts/service_form.html", {"form": form, "business": business, "title": "افزودن خدمت", "plan": plan})


@login_required
def service_update(request, pk):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    service = get_object_or_404(Service, pk=pk, business=business)
    plan = _current_plan(request.user)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service, business=business, plan=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "خدمت بروزرسانی شد.")
            return redirect("accounts:services")
    else:
        form = ServiceForm(instance=service, business=business, plan=plan)
    return render(request, "accounts/service_form.html", {"form": form, "business": business, "title": "ویرایش خدمت", "plan": plan})


@login_required
def working_hours(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    for weekday, _ in WorkingHour.WEEKDAY_CHOICES:
        WorkingHour.objects.get_or_create(business=business, weekday=weekday)

    if request.method == "POST":
        errors = []
        pending_updates = []
        for wh in business.working_hours.all():
            prefix = f"day_{wh.weekday}"
            data = {
                "weekday": wh.weekday,
                "is_open": request.POST.get(f"{prefix}_is_open") == "on",
                "opens_at": parse_time(request.POST.get(f"{prefix}_opens_at") or "") or wh.opens_at,
                "closes_at": parse_time(request.POST.get(f"{prefix}_closes_at") or "") or wh.closes_at,
                "break_starts_at": parse_time(request.POST.get(f"{prefix}_break_starts_at") or ""),
                "break_ends_at": parse_time(request.POST.get(f"{prefix}_break_ends_at") or ""),
            }
            form = WorkingHourForm(data=data, instance=wh)
            if form.is_valid():
                pending_updates.append(form)
            else:
                errors.append(f"{wh.get_weekday_display()}: {'، '.join(str(e) for field in form.errors.values() for e in field)}")
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            for form in pending_updates:
                form.save()
            messages.success(request, "ساعت‌های کاری ذخیره شد.")
            return redirect("accounts:working_hours")
    hours = business.working_hours.all()
    return render(request, "accounts/working_hours.html", {"business": business, "hours": hours})


@login_required
def time_blocks(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    if request.method == "POST":
        form = TimeBlockForm(request.POST)
        if form.is_valid():
            block = form.save(commit=False)
            block.business = business
            block.save()
            messages.success(request, "زمان موردنظر بسته شد.")
            return redirect("accounts:time_blocks")
    else:
        form = TimeBlockForm()
    blocks = business.time_blocks.all()
    return render(request, "accounts/time_blocks.html", {"form": form, "blocks": blocks, "business": business})


@login_required
def booking_list(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    status = request.GET.get("status")
    bookings = business.bookings.select_related("service", "staff").order_by("-starts_at")
    if status:
        bookings = bookings.filter(status=status)
    return render(request, "accounts/booking_list.html", {"business": business, "bookings": bookings, "statuses": Booking.STATUS_CHOICES, "current_status": status})


@login_required
def booking_update(request, pk):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    booking = get_object_or_404(Booking.objects.select_related("service", "staff", "business"), pk=pk, business=business)
    old_status = booking.status
    if request.method == "POST":
        form = BookingStatusForm(request.POST, choices=Booking.STATUS_CHOICES)
        if form.is_valid():
            booking.status = form.cleaned_data["status"]
            booking.save(update_fields=["status", "updated_at"])
            if booking.status != old_status:
                send_booking_status_notification(booking)
            messages.success(request, "وضعیت رزرو بروزرسانی شد.")
            return redirect("accounts:bookings")
    else:
        form = BookingStatusForm(initial={"status": booking.status}, choices=Booking.STATUS_CHOICES)
    return render(request, "accounts/booking_update.html", {"business": business, "booking": booking, "form": form})


@login_required
def booking_calendar(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=30)
    bookings = business.bookings.filter(starts_at__gte=start, starts_at__lt=end).select_related("service", "staff").order_by("starts_at")
    grouped = defaultdict(list)
    for booking in bookings:
        grouped[timezone.localtime(booking.starts_at).date()].append(booking)
    days = [{"date": start.date() + timedelta(days=i), "bookings": grouped.get(start.date() + timedelta(days=i), [])} for i in range(30)]
    return render(request, "accounts/booking_calendar.html", {"business": business, "days": days})


@login_required
def reports(request):
    business = get_object_or_404(BusinessProfile, owner=request.user)
    plan = _current_plan(request.user)
    if plan and not plan.advanced_reports:
        messages.info(request, "گزارش‌های پیشرفته در پلن فعلی فعال نیست؛ این صفحه فقط خلاصه پایه را نمایش می‌دهد.")

    now = timezone.localtime()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    bookings = business.bookings.filter(created_at__gte=month_start)
    status_labels = dict(Booking.STATUS_CHOICES)
    status_summary = [
        {"status": row["status"], "label": status_labels.get(row["status"], row["status"]), "total": row["total"]}
        for row in bookings.values("status").annotate(total=Count("id")).order_by("status")
    ]
    service_summary = bookings.values("service__title").annotate(total=Count("id"), income=Sum("payable_amount")).order_by("-total")[:10]
    day_summary = (
        bookings.annotate(day=TruncDate("starts_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    totals = {
        "all": bookings.count(),
        "paid_income": bookings.filter(is_paid=True).aggregate(total=Sum("payable_amount"))["total"] or 0,
        "cancelled": bookings.filter(status__in=[Booking.STATUS_CANCELLED_BY_CUSTOMER, Booking.STATUS_CANCELLED_BY_BUSINESS]).count(),
        "no_show": bookings.filter(status=Booking.STATUS_NO_SHOW).count(),
    }
    return render(request, "accounts/reports.html", {
        "business": business,
        "plan": plan,
        "totals": totals,
        "status_summary": status_summary,
        "service_summary": service_summary,
        "day_summary": day_summary,
        "statuses": status_labels,
    })


@login_required
def subscription(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).prefetch_related("features")
    current = getattr(request.user, "subscription", None)
    return render(request, "accounts/subscription.html", {"plans": plans, "current": current})

"""Small Jalali/Persian date helpers used by Nobtek.

The project intentionally keeps this dependency-free so the booking UI works
without adding external packages. It converts Gregorian dates to the official
Solar Hijri calendar used in Iran and returns Persian-digit labels.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from django.utils import timezone

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

JALALI_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]

# Python weekday(): Monday=0 ... Sunday=6
PERSIAN_WEEKDAYS = {
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنجشنبه",
    4: "جمعه",
    5: "شنبه",
    6: "یکشنبه",
}


def fa_digits(value) -> str:
    """Convert western digits in a value to Persian digits."""
    if value is None:
        return ""
    return str(value).translate(PERSIAN_DIGITS)


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    """Convert Gregorian date to Jalali date.

    Algorithm is the standard civil calendar conversion used by many lightweight
    Persian date utilities.
    """
    g_days_in_month_prefix = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621

    gy2 = gy + 1 if gm > 2 else gy
    days = (
        365 * gy
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
        - 80
        + gd
        + g_days_in_month_prefix[gm - 1]
    )

    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365

    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30

    return jy, jm, jd


def _as_local(value: date | datetime) -> date | datetime:
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            return timezone.localtime(value)
        return timezone.make_aware(value)
    return value


def jalali_parts(value: date | datetime) -> tuple[int, int, int]:
    value = _as_local(value)
    return gregorian_to_jalali(value.year, value.month, value.day)


def jalali_numeric(value: date | datetime) -> str:
    jy, jm, jd = jalali_parts(value)
    return fa_digits(f"{jy:04d}/{jm:02d}/{jd:02d}")


def jalali_date_label(value: date | datetime, *, with_weekday: bool = True) -> str:
    value = _as_local(value)
    jy, jm, jd = jalali_parts(value)
    base = f"{fa_digits(jd)} {JALALI_MONTHS[jm - 1]} {fa_digits(jy)}"
    if with_weekday:
        return f"{PERSIAN_WEEKDAYS[value.weekday()]} {base}"
    return base


def jalali_datetime_label(value: datetime) -> str:
    value = _as_local(value)
    return f"{jalali_date_label(value)}، ساعت {fa_digits(value.strftime('%H:%M'))}"


def jalali_short_day(value: date | datetime) -> str:
    value = _as_local(value)
    jy, jm, jd = jalali_parts(value)
    return f"{fa_digits(jd)} {JALALI_MONTHS[jm - 1]}"


def persian_weekday(value: date | datetime) -> str:
    value = _as_local(value)
    return PERSIAN_WEEKDAYS[value.weekday()]


def relative_day_label(value: date | datetime) -> str:
    value = _as_local(value)
    target_date = value.date() if isinstance(value, datetime) else value
    today = timezone.localdate()
    if target_date == today:
        return "امروز"
    tomorrow = today + timedelta(days=1)
    if target_date == tomorrow:
        return "فردا"
    return persian_weekday(value)

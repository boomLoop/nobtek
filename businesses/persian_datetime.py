"""Small Persian date helpers for Nobtek.

The project intentionally stays dependency-light, so Jalali conversion is implemented
here instead of requiring a third-party package. All helpers are display-only and do
not change the Gregorian datetimes used for validation/storage.
"""

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

JALALI_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

# Python weekday(): Monday=0 ... Sunday=6
PERSIAN_WEEKDAYS = [
    "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه",
]


def fa_number(value) -> str:
    if value is None:
        return ""
    return str(value).translate(PERSIAN_DIGITS)


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    """Convert Gregorian date to Jalali date.

    Algorithm based on the common arithmetic conversion used by jalaali-js and
    many Persian date libraries. It is deterministic and enough for UI display.
    """
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
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
        + g_d_m[gm - 1]
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


def jalali_parts(dt) -> tuple[int, int, int]:
    return gregorian_to_jalali(dt.year, dt.month, dt.day)


def persian_weekday(dt) -> str:
    return PERSIAN_WEEKDAYS[dt.weekday()]


def persian_time(dt) -> str:
    return dt.strftime("%H:%M").translate(PERSIAN_DIGITS)


def persian_date_short(dt) -> str:
    jy, jm, jd = jalali_parts(dt)
    return f"{fa_number(jd)} {JALALI_MONTHS[jm - 1]}"


def persian_date_full(dt, include_year: bool = True) -> str:
    jy, jm, jd = jalali_parts(dt)
    text = f"{persian_weekday(dt)} {fa_number(jd)} {JALALI_MONTHS[jm - 1]}"
    if include_year:
        text += f" {fa_number(jy)}"
    return text

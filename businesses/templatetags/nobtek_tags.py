from django import template

register = template.Library()

from businesses.persian_datetime import fa_number as _fa_number, persian_date_full, persian_date_short, persian_time



@register.filter
def fa_number(value):
    return _fa_number(value)


@register.filter
def toman(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    return _fa_number(f"{value:,}") + " تومان"


@register.filter
def duration_label(minutes):
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return minutes
    if minutes < 60:
        return _fa_number(minutes) + " دقیقه"
    hours = minutes // 60
    rest = minutes % 60
    if rest:
        return _fa_number(hours) + " ساعت و " + _fa_number(rest) + " دقیقه"
    return _fa_number(hours) + " ساعت"


@register.filter
def jalali_date(value):
    if not value:
        return ""
    return persian_date_full(value)


@register.filter
def jalali_date_short(value):
    if not value:
        return ""
    return persian_date_short(value)


@register.filter
def fa_time(value):
    if not value:
        return ""
    return persian_time(value)

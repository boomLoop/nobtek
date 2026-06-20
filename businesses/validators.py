import os
import re

from django.core.exceptions import ValidationError

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
IRAN_MOBILE_RE = re.compile(r"^09\d{9}$")


def normalize_digits(value: str) -> str:
    return (value or "").translate(FA_DIGITS).strip()


def normalize_phone(value: str) -> str:
    value = normalize_digits(value)
    value = value.replace(" ", "").replace("-", "")
    if value.startswith("+98"):
        value = "0" + value[3:]
    elif value.startswith("0098"):
        value = "0" + value[4:]
    return value


def validate_iran_mobile(value: str) -> str:
    phone = normalize_phone(value)
    if not IRAN_MOBILE_RE.match(phone):
        raise ValidationError("شماره موبایل باید با فرمت معتبر ایران وارد شود؛ مثل 09123456789.")
    return phone


def validate_image_file(uploaded_file, *, max_mb: int = 4) -> None:
    if not uploaded_file:
        return
    max_size = max_mb * 1024 * 1024
    if uploaded_file.size > max_size:
        raise ValidationError(f"حجم تصویر نباید بیشتر از {max_mb} مگابایت باشد.")
    ext = os.path.splitext(uploaded_file.name or "")[1].lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
    if ext not in allowed_exts:
        raise ValidationError("فرمت تصویر باید یکی از JPG، PNG یا WEBP باشد.")
    content_type = getattr(uploaded_file, "content_type", "") or ""
    if content_type and not content_type.startswith("image/"):
        raise ValidationError("فایل انتخاب‌شده تصویر معتبر نیست.")

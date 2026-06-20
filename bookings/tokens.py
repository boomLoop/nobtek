from django.core import signing

CANCEL_BOOKING_SALT = "nobtek.booking.cancel.v1"


def make_cancel_token(booking) -> str:
    signer = signing.TimestampSigner(salt=CANCEL_BOOKING_SALT)
    value = f"{booking.pk}:{booking.tracking_code}:{int(booking.starts_at.timestamp())}"
    return signer.sign(value)


def validate_cancel_token(booking, token: str, *, max_age: int = 60 * 60 * 24 * 45) -> bool:
    if not token:
        return False
    signer = signing.TimestampSigner(salt=CANCEL_BOOKING_SALT)
    try:
        value = signer.unsign(token, max_age=max_age)
    except signing.BadSignature:
        return False
    expected = f"{booking.pk}:{booking.tracking_code}:{int(booking.starts_at.timestamp())}"
    return value == expected

from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from businesses.models import BusinessProfile, Service, WorkingHour
from .forms import PublicBookingForm
from .models import Booking, PaymentTransaction
from .tokens import make_cancel_token, validate_cancel_token


class BookingSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.business = BusinessProfile.objects.create(owner=self.user, title="سالن تست", slug="salon-test", cancellation_hours=1)
        self.tomorrow = timezone.localdate() + timedelta(days=1)
        WorkingHour.objects.create(
            business=self.business,
            weekday=self.tomorrow.weekday(),
            opens_at=time(9, 0),
            closes_at=time(18, 0),
            is_open=True,
        )
        self.service = Service.objects.create(
            business=self.business,
            title="اصلاح",
            price=200000,
            duration_minutes=30,
            payment_mode=Service.PAYMENT_FULL,
        )
        self.booking = Booking.objects.create(
            business=self.business,
            service=self.service,
            customer_name="مینا",
            customer_phone="09123456789",
            starts_at=timezone.make_aware(datetime.combine(self.tomorrow, time(11, 0))),
            ends_at=timezone.make_aware(datetime.combine(self.tomorrow, time(11, 30))),
            status=Booking.STATUS_AWAITING_PAYMENT,
        )
        PaymentTransaction.objects.create(booking=self.booking, amount=self.booking.payable_amount)

    def test_booking_detail_exposes_valid_cancel_token(self):
        token = make_cancel_token(self.booking)
        self.assertTrue(validate_cancel_token(self.booking, token))
        self.assertFalse(validate_cancel_token(self.booking, token + "x"))

    def test_demo_payment_requires_post(self):
        url = reverse("bookings:pay_demo", kwargs={"tracking_code": self.booking.tracking_code})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertTrue(self.booking.is_paid)
        self.assertEqual(self.booking.status, Booking.STATUS_CONFIRMED)

    def test_cancel_requires_token(self):
        url = reverse("bookings:cancel", kwargs={"tracking_code": self.booking.tracking_code})
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_AWAITING_PAYMENT)

        token = make_cancel_token(self.booking)
        response = self.client.post(url, {"token": token}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED_BY_CUSTOMER)

    def test_public_form_normalizes_persian_mobile_digits(self):
        slot_start = timezone.now().replace(microsecond=0)
        form = PublicBookingForm(
            data={
                "slot": slot_start.isoformat(),
                "customer_name": "علی رضایی",
                "customer_phone": "۰۹۱۲۳۴۵۶۷۸۹",
                "customer_email": "",
                "notes": "",
                "accept_policy": "on",
            },
            slots=[{"start": slot_start, "end": slot_start + timedelta(minutes=30)}],
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["customer_phone"], "09123456789")

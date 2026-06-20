from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from bookings.models import Booking
from .availability import is_slot_available
from .models import BusinessProfile, Service, TimeBlock, WorkingHour, get_available_slots


class AvailabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.business = BusinessProfile.objects.create(owner=self.user, title="کلینیک تست", slug="clinic-test")
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
            title="مشاوره",
            price=100000,
            duration_minutes=60,
            buffer_minutes=15,
            capacity=1,
        )

    def aware(self, hour, minute=0):
        return timezone.make_aware(datetime.combine(self.tomorrow, time(hour, minute)))

    def test_buffer_minutes_blocks_next_slot_until_buffer_ends(self):
        Booking.objects.create(
            business=self.business,
            service=self.service,
            customer_name="علی",
            customer_phone="09123456789",
            starts_at=self.aware(10, 0),
            ends_at=self.aware(11, 0),
            status=Booking.STATUS_CONFIRMED,
        )

        self.assertFalse(is_slot_available(self.service, self.aware(11, 0)).ok)
        self.assertTrue(is_slot_available(self.service, self.aware(11, 15)).ok)

    def test_time_block_hides_overlapping_slot(self):
        TimeBlock.objects.create(
            business=self.business,
            title="جلسه داخلی",
            starts_at=self.aware(12, 0),
            ends_at=self.aware(13, 0),
        )

        self.assertFalse(is_slot_available(self.service, self.aware(12, 0)).ok)
        self.assertTrue(is_slot_available(self.service, self.aware(13, 0)).ok)

    def test_available_slots_are_generated_inside_working_hours(self):
        slots = get_available_slots(self.service, days=2)
        starts = {timezone.localtime(slot["start"]).time() for slot in slots if timezone.localtime(slot["start"]).date() == self.tomorrow}
        self.assertIn(time(9, 0), starts)
        self.assertNotIn(time(18, 0), starts)

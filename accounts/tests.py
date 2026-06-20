from datetime import time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from businesses.models import BusinessProfile, Service, StaffMember, WorkingHour
from plans.models import SubscriptionPlan, UserSubscription


class DashboardSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.plan = SubscriptionPlan.objects.create(name="طلایی", code=SubscriptionPlan.PLAN_GOLD, max_services=10, max_staff=5, online_payment=True, deposit_payment=True, advanced_reports=True)
        UserSubscription.objects.create(user=self.user, plan=self.plan)
        self.business = BusinessProfile.objects.create(owner=self.user, title="کسب‌وکار تست", slug="biz-test")
        WorkingHour.objects.create(business=self.business, weekday=0, opens_at=time(9), closes_at=time(18), is_open=True)
        self.staff = StaffMember.objects.create(business=self.business, full_name="کارمند تست")
        self.service = Service.objects.create(business=self.business, staff=self.staff, title="خدمت تست", price=100000)
        self.client.force_login(self.user)

    def test_dashboard_pages_render(self):
        names = [
            "accounts:dashboard",
            "accounts:services",
            "accounts:staff",
            "accounts:working_hours",
            "accounts:time_blocks",
            "accounts:bookings",
            "accounts:calendar",
            "accounts:reports",
            "accounts:subscription",
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_service_form_rejects_payment_when_plan_disallows_it(self):
        self.plan.online_payment = False
        self.plan.deposit_payment = False
        self.plan.save(update_fields=["online_payment", "deposit_payment"])
        response = self.client.post(reverse("accounts:service_create"), {
            "title": "خدمت پرداختی",
            "price": "100000",
            "duration_minutes": "30",
            "buffer_minutes": "0",
            "capacity": "1",
            "payment_mode": Service.PAYMENT_FULL,
            "deposit_amount": "0",
            "deposit_percent": "0",
            "is_active": "on",
            "order": "0",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "پرداخت کامل آنلاین در پلن فعلی فعال نیست")

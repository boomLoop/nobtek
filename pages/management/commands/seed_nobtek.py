from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import AccountProfile
from bookings.models import Booking, PaymentTransaction
from businesses.models import BusinessCategory, BusinessProfile, Service, WorkingHour
from pages.models import FAQ, SiteSetting, Testimonial
from plans.models import PlanFeature, SubscriptionPlan, UserSubscription


class Command(BaseCommand):
    help = "Seed Nobtek with Persian demo content, plans, categories and sample bookings."

    def handle(self, *args, **options):
        setting, _ = SiteSetting.objects.get_or_create(
            pk=1,
            defaults={
                "site_name": "نوبتک",
                "tagline": "لینک رزرو آنلاین برای هر کسب‌وکار",
                "contact_phone": "۰۲۱-۱۲۳۴۵۶۷۸",
                "contact_email": "hello@nobtek.ir",
                "address": "تهران، ایران",
            },
        )

        categories = [
            ("زیبایی و سلامت", "آرایشگاه، ناخن، میکاپ، ماساژ، پوست و مو"),
            ("پزشکی و درمانی", "پزشک، دندان‌پزشک، روانشناس، فیزیوتراپی"),
            ("آموزش", "معلم خصوصی، آموزشگاه، کلاس زبان، موسیقی"),
            ("ورزش", "مربی، باشگاه، یوگا، زمین فوتبال، استخر"),
            ("مشاوره", "حقوقی، مالی، مهاجرت، کسب‌وکار، تحصیلی"),
            ("فضا و مکان", "سالن، اتاق جلسه، استودیو، فضای کار اشتراکی"),
            ("خدمات فنی", "تعمیرکار، برق‌کار، لوله‌کش، سرویس‌کار"),
            ("تفریح و سرگرمی", "اتاق فرار، تور، رویداد، بازی"),
            ("عکاسی و مراسم", "آتلیه، فیلم‌بردار، سالن مراسم"),
            ("حیوانات خانگی", "دامپزشک، آرایش حیوانات، پانسیون"),
        ]
        category_objects = {}
        for order, (name, desc) in enumerate(categories, start=1):
            obj, _ = BusinessCategory.objects.update_or_create(
                name=name,
                defaults={"description": desc, "order": order, "is_active": True},
            )
            category_objects[name] = obj

        plan_data = [
            {
                "name": "رایگان", "code": "free", "monthly_price": 0, "yearly_price": 0,
                "max_services": 3, "max_bookings_per_month": 30, "max_staff": 1, "sms_credit": 0,
                "online_payment": False, "deposit_payment": False, "remove_branding": False,
                "description": "برای تست محصول و کسب‌وکارهای تازه‌کار.", "order": 1,
                "features": ["صفحه اختصاصی", "۳ خدمت", "۳۰ رزرو ماهانه", "نمایش برند نوبتک"],
            },
            {
                "name": "نقره‌ای", "code": "silver", "monthly_price": 399000, "yearly_price": 3990000,
                "max_services": 20, "max_bookings_per_month": 200, "max_staff": 3, "sms_credit": 50,
                "online_payment": True, "deposit_payment": True, "remove_branding": False,
                "description": "برای افراد مستقل و کسب‌وکارهای کوچک.", "order": 2, "is_featured": True,
                "features": ["پرداخت آنلاین", "دریافت بیعانه", "مدیریت مشتری‌ها", "گزارش رزرو"],
            },
            {
                "name": "طلایی", "code": "gold", "monthly_price": 899000, "yearly_price": 8990000,
                "max_services": 100, "max_bookings_per_month": 1000, "max_staff": 10, "sms_credit": 300,
                "online_payment": True, "deposit_payment": True, "remove_branding": True, "advanced_reports": True,
                "description": "برای سالن‌ها، کلینیک‌ها، آموزشگاه‌ها و تیم‌های حرفه‌ای.", "order": 3,
                "features": ["حذف برندینگ", "گزارش مالی", "خروجی اکسل", "پشتیبانی اولویت‌دار"],
            },
            {
                "name": "سازمانی", "code": "enterprise", "monthly_price": 0, "yearly_price": 0,
                "max_services": 1000, "max_bookings_per_month": 10000, "max_staff": 100, "sms_credit": 2000,
                "online_payment": True, "deposit_payment": True, "remove_branding": True, "custom_domain": True, "advanced_reports": True,
                "description": "برای مجموعه‌های چند شعبه‌ای و نیازهای اختصاصی.", "order": 4,
                "features": ["چند شعبه", "دامنه اختصاصی", "گزارش پیشرفته", "امکانات سفارشی"],
            },
        ]
        for item in plan_data:
            features = item.pop("features")
            plan, _ = SubscriptionPlan.objects.update_or_create(code=item["code"], defaults=item)
            plan.features.all().delete()
            for index, feature in enumerate(features, start=1):
                PlanFeature.objects.create(plan=plan, title=feature, order=index)

        FAQ.objects.all().delete()
        faqs = [
            ("نوبتک دقیقاً چه کاری انجام می‌دهد؟", "نوبتک برای کسب‌وکار شما یک صفحه رزرو آنلاین می‌سازد تا مشتری‌ها بدون تماس تلفنی زمان مناسب را انتخاب کنند."),
            ("آیا فقط برای آرایشگاه است؟", "خیر، هر خدمت، کلاس، مکان یا ظرفیت قابل رزرو می‌تواند داخل نوبتک مدیریت شود."),
            ("در نسخه رایگان چه محدودیتی دارم؟", "پنل رایگان برای تست اولیه است و تعداد خدمات و رزرو ماهانه محدود دارد."),
            ("پرداخت آنلاین واقعی فعال است؟", "در این نسخه ساختار پرداخت آماده شده و پرداخت آزمایشی قرار دارد؛ درگاه واقعی بعداً متصل می‌شود."),
        ]
        for i, (q, a) in enumerate(faqs, start=1):
            FAQ.objects.create(question=q, answer=a, order=i)

        Testimonial.objects.all().delete()
        Testimonial.objects.create(full_name="سارا احمدی", role="مدیر سالن زیبایی", quote="با نوبتک مشتری‌ها بدون تماس تلفنی وقت می‌گیرند و برنامه کاری ما مرتب‌تر شده است.", order=1)
        Testimonial.objects.create(full_name="امیر رضایی", role="مشاور کسب‌وکار", quote="لینک رزرو را در بیو اینستاگرام گذاشتم و مدیریت جلسه‌ها خیلی ساده‌تر شد.", order=2)
        Testimonial.objects.create(full_name="مریم کریمی", role="مدیر آموزشگاه", quote="برای کلاس‌های خصوصی و گروهی خیلی کاربردی است؛ مخصوصاً ظرفیت و زمان‌بندی.", order=3)

        admin_user, created = User.objects.get_or_create(username="admin", defaults={"email": "admin@nobtek.ir", "is_staff": True, "is_superuser": True})
        if created:
            admin_user.set_password("admin12345")
            admin_user.save()
        else:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save(update_fields=["is_staff", "is_superuser"])

        owner, created = User.objects.get_or_create(username="demo", defaults={"email": "demo@nobtek.ir", "first_name": "دمو"})
        if created:
            owner.set_password("demo12345")
            owner.save()
        AccountProfile.objects.get_or_create(user=owner, defaults={"full_name": "کاربر دمو", "phone": "09120000000", "is_phone_verified": True})
        silver = SubscriptionPlan.objects.get(code="silver")
        UserSubscription.objects.update_or_create(user=owner, defaults={"plan": silver, "is_active": True, "ends_at": timezone.now() + timezone.timedelta(days=365)})

        business, _ = BusinessProfile.objects.update_or_create(
            owner=owner,
            defaults={
                "category": category_objects["مشاوره"],
                "title": "مشاوره نوین",
                "slug": "moshavere-novin",
                "short_description": "رزرو جلسه مشاوره کسب‌وکار، مهاجرت و مسیر شغلی",
                "description": "این یک صفحه نمونه برای تست منطق رزرو نوبتک است. همه اطلاعات از پنل قابل تغییر است.",
                "business_type": BusinessProfile.TYPE_BOTH,
                "city": "تهران",
                "phone": "09120000000",
                "address": "تهران، خیابان نمونه، پلاک ۱۰",
                "booking_policy": "لغو رزرو تا ۲۴ ساعت قبل امکان‌پذیر است. برای رزروهای دارای بیعانه، قوانین بازگشت وجه توسط کسب‌وکار مشخص می‌شود.",
                "is_verified": True,
                "is_published": True,
            },
        )
        for weekday in [5, 6, 0, 1, 2, 3, 4]:
            WorkingHour.objects.update_or_create(
                business=business,
                weekday=weekday,
                defaults={"is_open": weekday != 4},
            )

        service1, _ = Service.objects.update_or_create(
            business=business,
            title="جلسه مشاوره ۶۰ دقیقه‌ای",
            defaults={
                "description": "جلسه آنلاین یا حضوری برای بررسی مسئله و ارائه راهکار عملی.",
                "price": 500000,
                "duration_minutes": 60,
                "buffer_minutes": 15,
                "capacity": 1,
                "payment_mode": Service.PAYMENT_FIXED_DEPOSIT,
                "deposit_amount": 100000,
                "is_active": True,
                "order": 1,
            },
        )
        service2, _ = Service.objects.update_or_create(
            business=business,
            title="جلسه تعیین مسیر ۳۰ دقیقه‌ای",
            defaults={
                "description": "جلسه کوتاه برای شناخت نیاز و انتخاب مسیر همکاری.",
                "price": 250000,
                "duration_minutes": 30,
                "buffer_minutes": 10,
                "capacity": 1,
                "payment_mode": Service.PAYMENT_NONE,
                "is_active": True,
                "order": 2,
            },
        )

        if not Booking.objects.filter(business=business).exists():
            start = timezone.now() + timezone.timedelta(days=2)
            start = start.replace(hour=11, minute=0, second=0, microsecond=0)
            booking = Booking.objects.create(
                business=business, service=service1, customer_name="مشتری تست", customer_phone="09121111111",
                starts_at=start, ends_at=start + timezone.timedelta(minutes=60), status=Booking.STATUS_CONFIRMED,
                price=service1.price, is_paid=True,
            )
            PaymentTransaction.objects.create(booking=booking, amount=service1.required_payment_amount, status=PaymentTransaction.STATUS_SUCCESS, paid_at=timezone.now(), authority="DEMO-SEED")

        self.stdout.write(self.style.SUCCESS("Nobtek demo data seeded successfully."))
        self.stdout.write("Admin: admin / admin12345")
        self.stdout.write("Demo owner: demo / demo12345")

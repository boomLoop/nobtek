from django import forms
from django.utils import timezone

from .models import BusinessProfile, Service, StaffMember, TimeBlock, WorkingHour
from .validators import validate_image_file, validate_iran_mobile


class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = [
            "category", "title", "slug", "short_description", "description", "business_type", "city", "address",
            "phone", "instagram_url", "whatsapp_url", "website_url", "logo", "cover", "booking_policy", "cancellation_hours", "is_published",
        ]
        widgets = {
            "short_description": forms.TextInput(attrs={"placeholder": "مثلاً کلینیک زیبایی، مشاوره آنلاین، آموزشگاه زبان..."}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "booking_policy": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if not phone:
            return phone
        return validate_iran_mobile(phone)

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        validate_image_file(logo, max_mb=3)
        return logo

    def clean_cover(self):
        cover = self.cleaned_data.get("cover")
        validate_image_file(cover, max_mb=5)
        return cover

    def clean_cancellation_hours(self):
        value = self.cleaned_data.get("cancellation_hours") or 0
        if value > 720:
            raise forms.ValidationError("مهلت لغو نمی‌تواند بیشتر از ۳۰ روز باشد.")
        return value


class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ["full_name", "role", "phone", "is_active", "order"]

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if not phone:
            return phone
        return validate_iran_mobile(phone)


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "staff", "title", "description", "price", "duration_minutes", "buffer_minutes", "capacity", "payment_mode",
            "deposit_amount", "deposit_percent", "is_active", "order",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, business=None, plan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business
        self.plan = plan
        if business:
            self.fields["staff"].queryset = business.staff_members.filter(is_active=True)
        self.fields["staff"].required = False
        self.fields["duration_minutes"].help_text = "بین ۵ تا ۴۸۰ دقیقه."
        self.fields["buffer_minutes"].help_text = "این فاصله پس از پایان رزرو برای آماده‌سازی، ضدعفونی یا استراحت خالی می‌ماند."

    def clean_duration_minutes(self):
        value = self.cleaned_data.get("duration_minutes") or 0
        if value < 5 or value > 480:
            raise forms.ValidationError("مدت‌زمان خدمت باید بین ۵ تا ۴۸۰ دقیقه باشد.")
        return value

    def clean_buffer_minutes(self):
        value = self.cleaned_data.get("buffer_minutes") or 0
        if value > 240:
            raise forms.ValidationError("فاصله بعد از رزرو نمی‌تواند بیشتر از ۲۴۰ دقیقه باشد.")
        return value

    def clean_capacity(self):
        value = self.cleaned_data.get("capacity") or 0
        if value < 1 or value > 100:
            raise forms.ValidationError("ظرفیت هر بازه باید بین ۱ تا ۱۰۰ باشد.")
        return value

    def clean(self):
        cleaned = super().clean()
        payment_mode = cleaned.get("payment_mode")
        price = cleaned.get("price") or 0
        deposit_amount = cleaned.get("deposit_amount") or 0
        deposit_percent = cleaned.get("deposit_percent") or 0

        if payment_mode != Service.PAYMENT_NONE and price <= 0:
            self.add_error("price", "برای خدمات دارای پرداخت، قیمت باید بیشتر از صفر باشد.")

        if payment_mode == Service.PAYMENT_FIXED_DEPOSIT:
            if deposit_amount <= 0:
                self.add_error("deposit_amount", "مبلغ بیعانه ثابت باید بیشتر از صفر باشد.")
            if price and deposit_amount > price:
                self.add_error("deposit_amount", "بیعانه ثابت نمی‌تواند از قیمت خدمت بیشتر باشد.")
        elif payment_mode != Service.PAYMENT_FIXED_DEPOSIT and deposit_amount:
            cleaned["deposit_amount"] = 0

        if payment_mode == Service.PAYMENT_PERCENT_DEPOSIT:
            if deposit_percent <= 0 or deposit_percent > 100:
                self.add_error("deposit_percent", "درصد بیعانه باید بین ۱ تا ۱۰۰ باشد.")
        elif payment_mode != Service.PAYMENT_PERCENT_DEPOSIT and deposit_percent:
            cleaned["deposit_percent"] = 0

        if self.plan:
            if payment_mode == Service.PAYMENT_FULL and not self.plan.online_payment:
                self.add_error("payment_mode", "پرداخت کامل آنلاین در پلن فعلی فعال نیست.")
            if payment_mode in {Service.PAYMENT_FIXED_DEPOSIT, Service.PAYMENT_PERCENT_DEPOSIT} and not self.plan.deposit_payment:
                self.add_error("payment_mode", "دریافت بیعانه در پلن فعلی فعال نیست.")

        return cleaned


class WorkingHourForm(forms.ModelForm):
    class Meta:
        model = WorkingHour
        fields = ["weekday", "opens_at", "closes_at", "break_starts_at", "break_ends_at", "is_open"]
        widgets = {
            "weekday": forms.HiddenInput(),
            "opens_at": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "closes_at": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "break_starts_at": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "break_ends_at": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def clean(self):
        cleaned = super().clean()
        opens_at = cleaned.get("opens_at")
        closes_at = cleaned.get("closes_at")
        break_start = cleaned.get("break_starts_at")
        break_end = cleaned.get("break_ends_at")
        is_open = cleaned.get("is_open")

        if is_open and opens_at and closes_at and opens_at >= closes_at:
            raise forms.ValidationError("ساعت پایان کار باید بعد از ساعت شروع باشد.")
        if bool(break_start) != bool(break_end):
            raise forms.ValidationError("برای زمان استراحت، هم شروع و هم پایان را وارد کنید.")
        if break_start and break_end:
            if break_start >= break_end:
                raise forms.ValidationError("پایان استراحت باید بعد از شروع استراحت باشد.")
            if opens_at and closes_at and not (opens_at < break_start < break_end < closes_at):
                raise forms.ValidationError("زمان استراحت باید داخل بازه کاری باشد.")
        return cleaned


class TimeBlockForm(forms.ModelForm):
    class Meta:
        model = TimeBlock
        fields = ["title", "starts_at", "ends_at"]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def clean(self):
        cleaned = super().clean()
        starts_at = cleaned.get("starts_at")
        ends_at = cleaned.get("ends_at")
        if starts_at and ends_at:
            if starts_at >= ends_at:
                raise forms.ValidationError("زمان پایان باید بعد از زمان شروع باشد.")
            if ends_at < timezone.now():
                raise forms.ValidationError("امکان ثبت زمان بسته در گذشته وجود ندارد.")
        return cleaned

from django import forms

from businesses.persian_datetime import persian_date_full, persian_time
from businesses.validators import validate_iran_mobile


class PublicBookingForm(forms.Form):
    slot = forms.ChoiceField(widget=forms.RadioSelect, label="زمان رزرو")
    customer_name = forms.CharField(label="نام و نام خانوادگی", max_length=120, widget=forms.TextInput(attrs={"placeholder": "مثلاً علی رضایی"}))
    customer_phone = forms.CharField(label="شماره موبایل", max_length=32, widget=forms.TextInput(attrs={"placeholder": "مثلاً 09123456789"}))
    customer_email = forms.EmailField(label="ایمیل", required=False, widget=forms.EmailInput(attrs={"placeholder": "اختیاری"}))
    notes = forms.CharField(label="توضیحات", required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "توضیح اختیاری برای کسب‌وکار"}))
    accept_policy = forms.BooleanField(label="قوانین رزرو را می‌پذیرم", required=True)

    def __init__(self, *args, slots=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        for slot in slots or []:
            start = slot["start"]
            label = f"{persian_date_full(start)} - ساعت {persian_time(start)}"
            choices.append((start.isoformat(), label))
        self.fields["slot"].choices = choices

    def clean_customer_phone(self):
        return validate_iran_mobile(self.cleaned_data.get("customer_phone", ""))


class BookingStatusForm(forms.Form):
    status = forms.ChoiceField(label="وضعیت", choices=[])

    def __init__(self, *args, choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = choices or []

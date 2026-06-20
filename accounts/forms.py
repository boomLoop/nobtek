from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.text import slugify

from businesses.models import BusinessCategory, BusinessProfile, WorkingHour
from businesses.validators import validate_iran_mobile
from plans.models import UserSubscription
from .models import AccountProfile


class PersianAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="نام کاربری یا ایمیل")
    password = forms.CharField(label="رمز عبور", widget=forms.PasswordInput)


class BusinessRegistrationForm(UserCreationForm):
    full_name = forms.CharField(label="نام و نام خانوادگی", max_length=120)
    phone = forms.CharField(label="شماره موبایل", max_length=32)
    email = forms.EmailField(label="ایمیل", required=False)
    business_title = forms.CharField(label="نام کسب‌وکار", max_length=140)
    category = forms.ModelChoiceField(label="دسته‌بندی", queryset=BusinessCategory.objects.filter(is_active=True), required=False)
    city = forms.CharField(label="شهر", max_length=80, required=False)
    slug = forms.SlugField(label="لینک اختصاصی", max_length=160, allow_unicode=True, help_text="مثلاً: clinic-novin یا ali-coach")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "full_name", "phone", "email", "business_title", "category", "city", "slug", "password1", "password2"]

    def clean_slug(self):
        slug = slugify(self.cleaned_data["slug"], allow_unicode=True)
        if not slug:
            raise forms.ValidationError("لینک اختصاصی معتبر نیست.")
        if BusinessProfile.objects.filter(slug=slug).exists():
            raise forms.ValidationError("این لینک اختصاصی قبلاً ثبت شده است.")
        return slug

    def clean_phone(self):
        return validate_iran_mobile(self.cleaned_data.get("phone", ""))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        first_name = self.cleaned_data["full_name"].split(" ", 1)[0]
        user.first_name = first_name
        if commit:
            user.save()
            AccountProfile.objects.create(
                user=user,
                full_name=self.cleaned_data["full_name"],
                phone=self.cleaned_data["phone"],
            )
            UserSubscription.create_default_for(user)
            business = BusinessProfile.objects.create(
                owner=user,
                category=self.cleaned_data.get("category"),
                title=self.cleaned_data["business_title"],
                slug=self.cleaned_data["slug"],
                city=self.cleaned_data.get("city", ""),
                phone=self.cleaned_data["phone"],
                short_description="صفحه رزرو اختصاصی ساخته شده با نوبتک",
            )
            for weekday in [5, 6, 0, 1, 2, 3, 4]:
                WorkingHour.objects.create(business=business, weekday=weekday, is_open=(weekday != 4))
        return user

from django import forms
from .models import LeadMessage


class LeadMessageForm(forms.ModelForm):
    class Meta:
        model = LeadMessage
        fields = ["full_name", "phone", "email", "message"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "نام و نام خانوادگی"}),
            "phone": forms.TextInput(attrs={"placeholder": "شماره موبایل"}),
            "email": forms.EmailInput(attrs={"placeholder": "ایمیل اختیاری"}),
            "message": forms.Textarea(attrs={"placeholder": "پیام شما", "rows": 4}),
        }

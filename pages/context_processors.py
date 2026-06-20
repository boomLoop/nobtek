from .models import SiteSetting


def site_settings(request):
    setting = SiteSetting.objects.first()
    if not setting:
        setting = SiteSetting(site_name="نوبتک", tagline="لینک رزرو آنلاین برای هر کسب‌وکار")
    return {"site_setting": setting}

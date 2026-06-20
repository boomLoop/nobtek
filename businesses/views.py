from django.shortcuts import get_object_or_404, render

from .models import BusinessProfile


def public_profile(request, slug):
    business = get_object_or_404(
        BusinessProfile.objects.select_related("category", "owner").prefetch_related("services", "working_hours"),
        slug=slug,
        is_published=True,
    )
    services = business.services.filter(is_active=True).select_related("staff")
    return render(request, "businesses/public_profile.html", {
        "business": business,
        "services": services,
        "meta_title": f"رزرو آنلاین {business.title} در نوبتک",
        "meta_description": business.short_description or business.description[:180] or "صفحه رزرو آنلاین کسب‌وکار در نوبتک",
    })

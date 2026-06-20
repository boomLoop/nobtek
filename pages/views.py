from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from businesses.models import BusinessCategory, BusinessProfile
from plans.models import SubscriptionPlan
from .forms import LeadMessageForm
from .models import FAQ, Testimonial


def home(request):
    categories = BusinessCategory.objects.filter(is_active=True)[:10]
    plans = SubscriptionPlan.objects.filter(is_active=True).prefetch_related("features")
    testimonials = Testimonial.objects.filter(is_active=True)[:6]
    faqs = FAQ.objects.filter(is_active=True)[:8]
    sample_businesses = BusinessProfile.objects.filter(is_published=True).select_related("category")[:6]
    return render(request, "pages/home.html", {
        "categories": categories,
        "plans": plans,
        "testimonials": testimonials,
        "faqs": faqs,
        "sample_businesses": sample_businesses,
        "meta_title": "نوبتک | لینک رزرو آنلاین برای هر کسب‌وکار",
    })


def pricing(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).prefetch_related("features")
    return render(request, "pages/pricing.html", {"plans": plans, "meta_title": "تعرفه‌ها و پنل‌های نوبتک"})


def categories(request):
    categories = BusinessCategory.objects.filter(is_active=True)
    return render(request, "pages/categories.html", {"categories": categories, "meta_title": "دسته‌بندی‌های قابل رزرو در نوبتک"})


def contact(request):
    if request.method == "POST":
        form = LeadMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "پیام شما ثبت شد. به‌زودی با شما تماس می‌گیریم.")
            return redirect("pages:contact")
    else:
        form = LeadMessageForm()
    return render(request, "pages/contact.html", {"form": form, "meta_title": "تماس با نوبتک"})


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {settings.SITE_DOMAIN.rstrip('/')}{reverse('pages:sitemap')}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml(request):
    domain = settings.SITE_DOMAIN.rstrip("/")
    urls = [
        (reverse("pages:home"), "daily", "1.0"),
        (reverse("pages:pricing"), "weekly", "0.8"),
        (reverse("pages:categories"), "weekly", "0.8"),
        (reverse("pages:contact"), "monthly", "0.5"),
    ]
    businesses = BusinessProfile.objects.filter(is_published=True).only("slug", "updated_at")
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    today = timezone.now().date().isoformat()
    for path, freq, priority in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{domain}{path}</loc>")
        xml.append(f"    <lastmod>{today}</lastmod>")
        xml.append(f"    <changefreq>{freq}</changefreq>")
        xml.append(f"    <priority>{priority}</priority>")
        xml.append("  </url>")
    for business in businesses:
        xml.append("  <url>")
        xml.append(f"    <loc>{domain}{business.get_absolute_url()}</loc>")
        xml.append(f"    <lastmod>{business.updated_at.date().isoformat()}</lastmod>")
        xml.append("    <changefreq>weekly</changefreq>")
        xml.append("    <priority>0.7</priority>")
        xml.append("  </url>")
    xml.append("</urlset>")
    return HttpResponse("\n".join(xml), content_type="application/xml")

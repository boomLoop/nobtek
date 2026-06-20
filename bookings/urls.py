from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path("b/<slug:business_slug>/service/<int:service_id>/book/", views.create_booking, name="create"),
    path("booking/<str:tracking_code>/", views.booking_detail, name="detail"),
    path("booking/<str:tracking_code>/pay-demo/", views.demo_payment_success, name="pay_demo"),
    path("booking/<str:tracking_code>/cancel/", views.cancel_booking, name="cancel"),
]

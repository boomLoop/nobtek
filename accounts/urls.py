from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.NobtekLoginView.as_view(), name="login"),
    path("logout/", views.NobtekLogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/business/", views.business_settings, name="business_settings"),
    path("dashboard/staff/", views.staff_list, name="staff"),
    path("dashboard/staff/new/", views.staff_create, name="staff_create"),
    path("dashboard/staff/<int:pk>/edit/", views.staff_update, name="staff_update"),
    path("dashboard/services/", views.service_list, name="services"),
    path("dashboard/services/new/", views.service_create, name="service_create"),
    path("dashboard/services/<int:pk>/edit/", views.service_update, name="service_update"),
    path("dashboard/working-hours/", views.working_hours, name="working_hours"),
    path("dashboard/time-blocks/", views.time_blocks, name="time_blocks"),
    path("dashboard/bookings/", views.booking_list, name="bookings"),
    path("dashboard/bookings/<int:pk>/", views.booking_update, name="booking_update"),
    path("dashboard/calendar/", views.booking_calendar, name="calendar"),
    path("dashboard/reports/", views.reports, name="reports"),
    path("dashboard/subscription/", views.subscription, name="subscription"),
]

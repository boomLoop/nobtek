from django.urls import path
from . import views

app_name = "businesses"

urlpatterns = [
    path("b/<slug:slug>/", views.public_profile, name="public_profile"),
]

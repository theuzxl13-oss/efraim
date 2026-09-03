from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("eventos/", views.eventos, name="eventos"),
    path("atas/", views.atas, name="atas"),
]

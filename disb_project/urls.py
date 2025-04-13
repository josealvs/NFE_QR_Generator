from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    path("nfe/", include("disbapp.urls")),  # Rota /nfe/ -> views do app
    path("", lambda request: redirect("form-nfe")),  # Redireciona "/" para /nfe/
]

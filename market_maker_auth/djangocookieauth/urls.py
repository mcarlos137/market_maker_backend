from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include  # new import


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),  # new
]

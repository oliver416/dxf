from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from django.contrib.auth import urls
from django.contrib.auth import views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    url(r'accounts/', include('django.contrib.auth.urls')),
]

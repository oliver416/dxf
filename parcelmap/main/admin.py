from django.contrib import admin
from .models import Parcel


class CustomAdmin(admin.ModelAdmin):
    search_fields = ['status']

admin.site.register(Parcel, CustomAdmin)

admin.site.site_header ='Администрирование'

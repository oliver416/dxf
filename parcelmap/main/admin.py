from django.contrib import admin
from .models import Parcel

# admin.site.register(Parcel)

class CustomAdmin(admin.ModelAdmin):
    search_fields = ['status']

    # def test_function(self):
    #     return 'Something'

admin.site.register(Parcel, CustomAdmin)

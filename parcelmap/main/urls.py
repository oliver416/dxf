from django.urls import path, include
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('', admin.site.urls),
    # url(r'^$', include('django.contrib.auth.urls')),
    # path('upload/', views.upload_dxf),
    url('show_result/', views.upload_dxf),
    url('result/', views.result),
    url('save/', views.save_result),
    path('excel/', views.upload_excel),
    # url('show/', views.test_page, name='show'),
]

# from django.core.urlresolvers import reverse
# from django.views.generic.base import RedirectView

# url(r'^$', RedirectView.as_view(url=reverse('admin:index')))
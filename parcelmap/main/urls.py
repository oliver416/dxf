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
    url('show/', views.upload_dxf),
    path('excel/', views.upload_excel),
    # url('show/', views.test_page, name='show'),
    url('show2/', RedirectView.as_view(url='/')),
]

# from django.core.urlresolvers import reverse
# from django.views.generic.base import RedirectView

# url(r'^$', RedirectView.as_view(url=reverse('admin:index')))
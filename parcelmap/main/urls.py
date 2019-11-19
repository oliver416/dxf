from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    url('show_result/', views.upload_dxf),
    url('result/', views.result),
    url('save/', views.save_result),
    path('excel/', views.save_excel),
    url('save_excel_db/', views.save_excel_db),
    url('get_count_excel/', views.get_count_excel),
    url('get_base_count/', views.get_base_count)
]
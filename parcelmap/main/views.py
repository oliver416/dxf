import shutil, os
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError
from django.template import loader
from django.core.files.storage import FileSystemStorage
from .converter.dxf import read_dxf
from .converter.excel import read_excel
from .models import Parcel

def index(request):
    return render(request, 'main/index.html')


def upload_dxf(request):
    os.mkdir('./media')

    if request.method == 'POST':
        uploaded_file = request.FILES['dxf']
    else:
        return HttpResponseServerError('Неверный тип запроса') # TODO: file type check
    fs = FileSystemStorage()
    name = fs.save('./media/'+uploaded_file.name, uploaded_file)
    url = fs.url(name)
    read_dxf(url, 'main/templates/main/upload.html')

    shutil.rmtree('./media')
    return render(request, 'main/upload.html')


def upload_excel(request):
    os.mkdir('./media')

    if request.method == 'POST':
        uploaded_file = request.FILES['xls']
    else:
        return HttpResponseServerError('Неверный тип запроса')
    fs = FileSystemStorage()
    name = fs.save('./media/' + uploaded_file.name, uploaded_file)
    url = fs.url(name)
    excel = read_excel(url)

    Parcel.objects.all().delete()

    for row in excel.index:
        statuses = {
            'Продано ранее': 'Sold',
            'Свободно': 'Free',
            'Бронь': 'Booked'
        }
        parcel_id = excel.loc[row]['Номер участка']
        cadastral = excel.loc[row]['КН 1']
        cadastral_number = excel.loc[row]['КН 2']
        area = excel.loc[row]['Площадь']
        status = statuses[excel.loc[row]['Статус']]
        owner = excel.loc[row]['Собственник']
        price = excel.loc[row]['Цена базовая']
        unp = excel.loc[row]['УНП']
        name = excel.loc[row]['ФИО Покупателя']
        Parcel(parcel_id=parcel_id, cadastral=cadastral, cadastral_number=cadastral_number, area=area, status=status, owner=owner, price=price,
           unp=unp, name=name).save()

    shutil.rmtree('./media') # TODO: russian file names

    return render(request, 'main/test.html', {'var': 'Done'})

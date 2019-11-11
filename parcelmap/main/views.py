import shutil, os
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseServerError, Http404
from django.template import loader
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from .converter.dxf import read_dxf
from .converter.excel import read_excel
from .models import Parcel

@login_required
def index(request):
    return render(request, 'main/index.html')

@login_required
def upload_dxf(request):
    os.mkdir('./media')

    if request.method == 'POST':
        uploaded_file = request.FILES['dxf']
    else:
        return HttpResponseServerError('Неверный тип запроса') # TODO: file type check
    fs = FileSystemStorage()
    name = fs.save('./media/'+uploaded_file.name, uploaded_file)
    url = fs.url(name)
    # dxf_variables = read_dxf(url, 'main/templates/main/result.html')
    read_dxf(url, 'main/templates/main/result.html')

    shutil.rmtree('./media')
    # return render(request, 'main/show.html', {"parcel_data": dxf_variables['parcel_data'], "svg": dxf_variables['svg']})
    return render(request, 'main/show_result.html')

@login_required
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

    # TODO: FileExistsError at /show_result/

    return render(request, 'main/excel.html', {'var': 'Done'})


@login_required
def result(request):
    return render(request, 'main/result.html')


@login_required
def save_result(request):
    file_path = 'main/templates/main/result.html'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type="text/html")
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            return response
            # return render(request, 'main/save.html')
    # raise Http404
    return render(request, 'main/save.html')

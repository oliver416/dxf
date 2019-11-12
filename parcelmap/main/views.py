import shutil, os
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError, Http404
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from .converter.dxf import read_dxf
from .converter.excel import read_excel
from .models import Parcel

MEDIA_DIR = './media'
RESULT_PATH = 'main/templates/main/result.html'


@login_required
def index(request):
    count_rows = len(Parcel.objects.all())
    return render(request, 'main/index.html', {'count_rows': count_rows})

@login_required
def upload_dxf(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES['dxf']
        else:
            return HttpResponseServerError('Неверный тип запроса') # TODO: file type check
        fs = FileSystemStorage() # TODO: file empty check
        path = MEDIA_DIR + uploaded_file.name # TODO: columns check
        if os.path.exists(path):
            name = fs.save(path, uploaded_file)
        else:
            return HttpResponseServerError('Загруженный файл не существует')
        url = fs.url(name)
        read_dxf(url, RESULT_PATH)
    except Exception as e:
        return HttpResponseServerError('Ошибка загрузки DXF: '+ str(type(e).__name__) + ' ' + str(e))
    finally:
        shutil.rmtree(MEDIA_DIR)
        os.mkdir(MEDIA_DIR)
    return render(request, 'main/show_result.html')

@login_required
def upload_excel(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES['xls']
        else:
            return HttpResponseServerError('Неверный тип запроса')
        fs = FileSystemStorage()
        path = MEDIA_DIR + uploaded_file.name
        if os.path.exists(path):
            name = fs.save(path, uploaded_file)
        else:
            return HttpResponseServerError('Загруженный файл не существует проверьте формат файла')
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

    except Exception as e:
        if isinstance(e, KeyError):
            return HttpResponseServerError('Не обнаружена колонка: ' + str(e))
        else:
            return HttpResponseServerError('Ошибка загрузки Excel: '+ str(type(e).__name__) + ' ' + str(e))
    finally:
        shutil.rmtree(MEDIA_DIR)
        os.mkdir(MEDIA_DIR)
    # TODO: FileExistsError at /show_result/
    # TODO: add spinner (xls)

    return render(request, 'main/excel.html')


@login_required
def result(request):
    return render(request, 'main/result.html')


@login_required
def save_result(request):
    file_path = RESULT_PATH
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type="text/html")
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            return response
    raise Http404

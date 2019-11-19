import shutil, os, json
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError, Http404
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .converter.dxf import read_dxf
from .converter.excel import read_excel
from .models import Parcel, Excel

MEDIA_DIR = './media/'
RESULT_PATH = 'main/templates/main/result.html'


@login_required
def index(request):
    count_rows = len(Parcel.objects.all())
    return render(request, 'main/index.html', {'count_rows': count_rows})


@login_required
def upload_dxf(request):
    try:
        if request.method == 'POST':
            if not request.FILES:
                return HttpResponseServerError('Файл не выбран')
            uploaded_file = request.FILES['dxf']
            if uploaded_file.name.split('.')[1] != 'dxf':
                return HttpResponseServerError('Неверный формат файла')
        else:
            return HttpResponseServerError('Неверный тип запроса')
        fs = FileSystemStorage()
        path = MEDIA_DIR
        if os.path.exists(path):
            name = fs.save(path+uploaded_file.name, uploaded_file)
        else:
            return HttpResponseServerError('Загруженный файл не существует')
        read_dxf(name, RESULT_PATH)
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
            if not request.FILES:
                return HttpResponseServerError('Файл не выбран')
            uploaded_file = request.FILES['file']
            if uploaded_file.name.split('.')[-1] not in ['xls', 'xlsx', 'xlsm']:
                return HttpResponseServerError('Неверный формат файла')
        else:
            return HttpResponseServerError('Неверный тип запроса')
        fs = FileSystemStorage()
        path = MEDIA_DIR
        if os.path.exists(path):
            name = fs.save(path+uploaded_file.name, uploaded_file)
        else:
            return HttpResponseServerError('Загруженный файл не существует')
        excel = read_excel(name)

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


@login_required
def get_base_count(request):
    count = len(Parcel.objects.all())
    return JsonResponse({'parcels_count': count})


@login_required
def save_excel(request):
    try:
        if request.method == 'POST':
            if not request.FILES:
                return HttpResponseServerError('Файл не выбран')
            uploaded_file = request.FILES['file']
            if uploaded_file.name.split('.')[-1] not in ['xls', 'xlsx', 'xlsm']:
                return HttpResponseServerError('Неверный формат файла')
        else:
            return HttpResponseServerError('Неверный тип запроса')
        fs = FileSystemStorage()
        path = MEDIA_DIR
        if os.path.exists(path):
            name = fs.save(path + uploaded_file.name, uploaded_file)
        else:
            return HttpResponseServerError('Загруженный файл не существует')
        excel_content = read_excel(name)
        Excel.objects.all().delete()
        Excel(id=1, count_rows=excel_content.index.size, path=name).save()
        return JsonResponse({"name": name})
    except Exception as e:
        return HttpResponseServerError('Ошибка загрузки Excel: ' + str(type(e).__name__) + ' ' + str(e))


@login_required
def get_count_excel(request):
    count_excel = Excel.objects.get(id=1).count_rows
    count_db = json.loads(get_base_count(request).content)['parcels_count']
    if count_db > 0:
        count = count_db/count_excel
    else:
        count = 0
    return JsonResponse({"count": count})


@login_required
def save_excel_db(request):
    try:
        file_path = Excel.objects.get(id=1).path
        excel = read_excel(file_path)

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
            Parcel(parcel_id=parcel_id, cadastral=cadastral, cadastral_number=cadastral_number, area=area, status=status,
                   owner=owner, price=price,
                   unp=unp, name=name).save()
        return render(request, 'main/excel.html')
    except Exception as e:
        return HttpResponseServerError('Ошибка загрузки Excel: ' + str(type(e).__name__) + ' ' + str(e))
    finally:
        shutil.rmtree(MEDIA_DIR)
        os.mkdir(MEDIA_DIR)

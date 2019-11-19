from django.db import models


class Parcel(models.Model):
    PARCEL_STATUSES = [
        ('Sold','Продано ранее'),
        ('Free','Свободно'),
        ('Booked','Бронь'),
    ]

    id = models.AutoField(primary_key=True)
    parcel_id = models.IntegerField(verbose_name='Номер участка', unique=True)
    cadastral = models.CharField(max_length=20, verbose_name='КН1', blank=True)
    cadastral_number = models.CharField(max_length=20, verbose_name='КН2', blank=True)
    area = models.FloatField(max_length=20, verbose_name='Площадь')
    status = models.CharField(max_length=30, verbose_name='Статус', choices=PARCEL_STATUSES)
    owner = models.CharField(max_length=70, verbose_name='Собственник', blank=True)
    price = models.FloatField(max_length=30, verbose_name='Цена базовая')
    unp = models.CharField(max_length=10, verbose_name='УНП', blank=True)
    name = models.CharField(max_length=100, verbose_name='ФИО Покупателя', blank=True)

    def __str__(self):
        return 'Участок №'+str(self.parcel_id)

    class Meta:
        verbose_name = 'Участок'
        verbose_name_plural = 'Участки'

class Excel(models.Model):
    count_rows = models.IntegerField(blank=True)
    path = models.CharField(blank=True, max_length=200)

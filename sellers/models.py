# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Goods(models.Model):
    vk_photo_id = models.CharField(primary_key=True, max_length=256)
    photo_link = models.CharField(max_length=1024, blank=True, null=True)
    seller = models.ForeignKey('Sellers', models.DO_NOTHING, blank=True, null=True)
    descr = models.CharField(max_length=10240, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'goods'


class Sellers(models.Model):
    vk_id = models.IntegerField(primary_key=True)
    full_name = models.CharField(max_length=512, blank=True, null=True)
    city = models.CharField(max_length=512, blank=True, null=True)
    number_of_goods = models.IntegerField(blank=True, null=True)
    photo = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sellers'

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.conf import settings
from barahlochannel.settings import ChannelEnum


if settings.CHANNEL == ChannelEnum.FIX_SHOSSE:
    _GOODS_TABLE = 'barahlochannel_goods'
    _ALBUMS_TABLE = 'barahlochannel_albums'
elif settings.CHANNEL == ChannelEnum.MTB:
    _GOODS_TABLE = 'barahlochannel_mtb_goods'
    _ALBUMS_TABLE = 'barahlochannel_mtb_albums'


class BarahlochannelAlbums(models.Model):
    owner_id = models.BigIntegerField(primary_key=True)
    album_id = models.BigIntegerField()
    title = models.CharField(max_length=1024, blank=True, null=True)
    description = models.CharField(max_length=1024, blank=True, null=True)
    photo = models.CharField(max_length=1024, blank=True, null=True)

    def is_group(self):
        if self.owner_id < 0:
            return True
        return False

    class Meta:
        managed = False
        db_table = _ALBUMS_TABLE
        unique_together = (('owner_id', 'album_id'),)


class GoodsManager(models.Manager):
    def has_duplicates(self, photo_hash):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM {t} 
                WHERE hash = %s;
                """.format(t=self.model._meta.db_table), (photo_hash,))
            result = cursor.fetchone()
            return result[0]


class BarahlochannelGoods(models.Model):
    vk_owner_id = models.IntegerField(primary_key=True)
    vk_photo_id = models.IntegerField()
    photo_link = models.CharField(max_length=1024)
    seller = models.ForeignKey('Sellers', models.DO_NOTHING)
    descr = models.CharField(max_length=6666, blank=True, null=True)
    comments = models.CharField(max_length=1024, blank=True, null=True)
    tg_post_id = models.IntegerField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    hash = models.CharField(max_length=64, blank=True, null=True)

    objects = GoodsManager()

    def has_duplicates(self):
        if self.hash is None:
            return False
        return BarahlochannelGoods.objects.has_duplicates(self.hash) != 1

    def duplicates_number(self):
        return BarahlochannelGoods.objects.filter(hash=self.hash).count()

    class Meta:
        managed = False
        db_table = _GOODS_TABLE
        unique_together = (('vk_owner_id', 'vk_photo_id'),)


class Cities(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cities'


class Groups(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=1024, blank=True, null=True)
    screen_name = models.CharField(max_length=1024, blank=True, null=True)
    photo = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'groups'


class Sellers(models.Model):
    vk_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=256, blank=True, null=True)
    last_name = models.CharField(max_length=256, blank=True, null=True)
    city = models.ForeignKey(Cities, models.DO_NOTHING, blank=True, null=True)
    photo = models.CharField(max_length=1024, blank=True, null=True)

    def is_group(self):
        if self.vk_id < 0:
            return True
        return False

    def goods_counter(self):
        return BarahlochannelGoods.objects.filter(seller__vk_id=self.vk_id).count()

    class Meta:
        managed = False
        db_table = 'sellers'

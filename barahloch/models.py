from django.db import models
from django.contrib.postgres.fields import ArrayField
from enum import Enum, auto
import os

class CategoriesEnum(Enum):
    ROAD = "Шоссер"
    CYCLOCROSS = "Циклокросс"
    FIX = "Фикс"
    SINGLE = "Синглспид"
    GRAVEL = "Гревел"
    TOURING = "Туринг"
    FRAMES = "Рама"
    FORKS = "Вилка"
    RIMBRAKES = "Ободные тормоза"
    DISCBRAKES = "Дисковые тормоза"
    BRAKELEVERS = "Ручки"
    BRAKECABLES = "Тросики"
    HANDLEBARS = "Рули"
    STEMS = "Выносы"
    HEADSETS = "Рулевые"
    TOPCAPS = "Топкепы"
    SPACERS = "Проставочные кольца"
    BARTAPES = "Обмотки"
    GRIPS = "Грипсы"
    SADDLES = "Седла"
    SEATPOSTS = "Подседел"
    CLAMPS = "Зажим"
    GROUPSETS = "Групсеты"
    CHAINSETS = "Системы"
    CHAINS = "Цепи"
    BOTTOMBRACKETS = "Каретки"
    CHAINRINGS = "Звезды (перед)"
    SPROCKETS = "Звезды (зад)"
    FRONTDERAILLEURS = "Перед. переклюк"
    CASSETES = "Кассеты"
    FREEHUBS = "Барабаны"
    REARDERAILLEURS = "Зад. переклюк"
    GEARLEVERS = "Шифтеры"
    MECHHANGERS = "Петухи"
    GEARCABLES = "Тросики"
    PEDALS = "Педали"
    CLEATS = "Шипы"
    STRAPS = "Стрепы"
    TOECLIPS = "Туклипсы"
    CLEATCOVERS = "Бахилы"
    WHEELS = "Колеса"
    HUBS = "Втулки"
    TYRES = "Покрышки"
    RIMS = "Обода"
    TUBES = "Камеры"
    SPOKES = "Спицы"
    PUMPS = "Насосы"
    TOOLS = "Инструменты"
    STANDS = "Стойки и стенды"
    GLASSES = "Очки"
    LOCKS = "Замки"
    LIGHTS = "Фонари"
    BOTTLES = "Фляги"
    BOTTLECAGES = "Флягодержатели"
    COMPUTERS = "Велокомпы"
    MUDGUARDS = "Крылья"
    RACKS = "Багажники"
    TRAINERS = "Станки"
    BIKEBAGS = "Чехлы"
    FRAMEBAGS = "Боксы"
    BAUL = "Баулы"
    ROLLTOPS = "Роллтопы"
    MESSENGERS = "Мессенджеры"
    HANDLEBARBAGS = "Нарульные сумки"
    WAISTBAGS = "Поясные сумки"
    CLOTHING = "Одежда"
    FOOTWEAR = "Обувь"
    HELMETS = "Шлемы"


class CurrencyEnum(Enum):
    RUB = 'RUB/₽'
    USD = 'USD/$'
    EUR = 'EUR/€'
    UAH = 'UAH/Гривна'


class ShippingEnum(Enum):
    DO_NOT_SHIP = "Не отправляю"
    WILL_SHIP_BY_CUSTOMER = "За счет покупателя"
    WILL_SHIP_SAINT = "За свой счёт"


class ProductStateEnum(Enum):
    SHOW = 'в продаже'
    SOLD = 'продано/снято с продажи'
    HIDDEN = 'скрыт админом'


STATE_CHOICES = [(c.name, c.value) for c in ProductStateEnum]


class Albums(models.Model):
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
        db_table = 'albums'
        unique_together = (('owner_id', 'album_id'),)


class GoodsManager(models.Manager):
    def has_duplicates(self, photo_hash):
        if not photo_hash:
            return None
        found_none = photo_hash.find('None')
        if found_none != -1:
            return None
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM {t} 
                WHERE hash = %s;
                """.format(t=self.model._meta.db_table), (photo_hash,))
            result = cursor.fetchone()
            return result[0]


class VkGoods(models.Model):
    vk_owner_id = models.IntegerField()
    vk_photo_id = models.IntegerField()
    vk_album_id = models.IntegerField()
    photo_link = models.CharField(max_length=1024)
    photo_preview = models.CharField(max_length=1024)
    seller = models.ForeignKey('VkSellers', models.DO_NOTHING)
    descr = models.CharField(max_length=6666, blank=True, null=True)
    comments = models.CharField(max_length=1024, blank=True, null=True)
    tg_post_id = models.IntegerField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    hash = models.CharField(max_length=64, blank=True, null=True)
    state = models.TextField(blank=True, null=False, choices=STATE_CHOICES)

    objects = GoodsManager()

    def has_duplicates(self):
        if self.hash is None:
            return False
        return VkGoods.objects.has_duplicates(self.hash) != 1

    def duplicates_number(self):
        return VkGoods.objects.filter(hash=self.hash).count()

    def get_preview_photo(self):
        if not self.photo_preview:
            return self.photo_link
        return self.photo_preview

    def is_telegram(self):
        return False

    class Meta:
        managed = False
        db_table = 'goods'
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


class VkSellers(models.Model):
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
        return VkGoods.objects.filter(seller__vk_id=self.vk_id).count()

    def is_telegram(self):
        return False

    class Meta:
        managed = False
        db_table = 'sellers'


CATEGORY_CHOICES = [(c.name, c.value) for c in CategoriesEnum]
SHIP_CHOICES = [(s.name, s.value) for s in ShippingEnum]
CURRENCY_CHOICES = [(c.name, c.value) for c in CurrencyEnum]

# class TgGoods(models.Model):
#     CATEGORY_CHOICES = [(c.name, c.value) for c in CategoriesEnum]
#     SHIP_CHOICES = [(s.name, s.value) for s in ShippingEnum]
#     CURRENCY_CHOICES = [(c.name, c.value) for c in CurrencyEnum]
#
#     tg_user = models.ForeignKey('TgSellers', models.DO_NOTHING, blank=True, null=True)
#     photo_link = models.CharField(max_length=1024, blank=True, null=True)
#     caption = models.CharField(max_length=4096, blank=True, null=True)
#     descr = models.CharField(max_length=4096, blank=True, null=True)
#     tg_post_id = models.IntegerField(primary_key=True)
#     date = models.DateTimeField(blank=True, null=True)
#     hash = models.CharField(max_length=64, blank=True, null=True)
#     category = models.TextField(blank=True, null=True, choices=CATEGORY_CHOICES)
#     price = models.IntegerField(blank=True, null=True)
#     currency = models.TextField(blank=True, null=True, choices=CURRENCY_CHOICES)
#     ship = models.TextField(blank=True, null=True, choices=SHIP_CHOICES)
#     vk_owner_id = models.IntegerField(blank=True, null=True)
#     vk_photo_id = models.IntegerField(blank=True, null=True)
#     state = models.TextField(blank=True, null=False, choices=STATE_CHOICES)
#
#     objects = GoodsManager()
#
#     def has_duplicates(self):
#         if self.hash is None:
#             return False
#         return TgGoods.objects.has_duplicates(self.hash) != 1
#
#     def duplicates_number(self):
#         return TgGoods.objects.filter(hash=self.hash).count()
#
#     def get_preview_photo(self):
#         return self.photo_link
#
#     def is_telegram(self):
#         return True
#
#     class Meta:
#         managed = False
#         db_table = 'tg_goods'


class TgCyclingmarket(models.Model):
    tg_user = models.ForeignKey('TgSellers', models.DO_NOTHING, blank=True, null=True)
    tg_post_id = models.IntegerField(primary_key=True)
    caption = models.CharField(max_length=4096)
    descr = models.CharField(max_length=4096)
    price_str = models.CharField(max_length=4096, blank=True, null=True)
    price_rub = models.IntegerField(blank=True, null=True)
    city = models.ForeignKey(Cities, models.DO_NOTHING, blank=True, null=True)
    photo_link = ArrayField(models.CharField(max_length=1024))
    state = models.TextField(blank=True, null=False, choices=STATE_CHOICES)
    date = models.DateTimeField()
    hash = ArrayField(models.CharField(max_length=64))
    category = ArrayField(models.TextField(blank=True, null=True, choices=CATEGORY_CHOICES))
    condition = models.TextField(blank=True, null=True)  # This field type is a guess.
    ship = models.TextField(blank=True, null=True, choices=SHIP_CHOICES)

    def is_telegram(self):
        return True

    def get_preview_photo(self):
        photo_dir = '/static/img/cyclingmarket'
        return os.path.join(photo_dir, self.photo_link[0])

    def get_photo(self):
        photo_dir = '/static/img/cyclingmarket'
        return os.path.join(photo_dir, self.photo_link[0])

    #     def has_duplicates(self):
    #         if self.hash is None:
    #             return False
    #         return TgGoods.objects.has_duplicates(self.hash) != 1
    #
    #     def duplicates_number(self):
    #         return TgGoods.objects.filter(hash=self.hash).count()

    class Meta:
        managed = False
        db_table = 'tg_cyclingmarket'


class TgSellers(models.Model):
    tg_user_id = models.IntegerField(primary_key=True)
    full_name = models.CharField(max_length=512, blank=True, null=True)
    username = models.CharField(max_length=512, blank=True, null=True)
    city = models.ForeignKey(Cities, models.DO_NOTHING, blank=True, null=True)

    def goods_counter(self):
        return TgCyclingmarket.objects.filter(tg_user__tg_user_id=self.tg_user_id).count()

    def is_telegram(self):
        return True

    class Meta:
        managed = False
        db_table = 'tg_sellers'

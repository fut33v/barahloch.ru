from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from django.conf import settings
from barahlochannel.settings import ChannelEnum
from django.db.models import Count
from .models import Sellers, BarahlochannelGoods, BarahlochannelAlbums, Groups, Cities

_GOODS = BarahlochannelGoods
_ALBUMS = BarahlochannelAlbums

if settings.CHANNEL == ChannelEnum.FIX_SHOSSE:
    _CHANNEL = "barahlochannel"
elif settings.CHANNEL == ChannelEnum.MTB:
    _CHANNEL = "barahlochannel_mtb"


def sellers_list(request):
    sellers_for_goods = _GOODS.objects.values('seller_id')

    sellers = Sellers.objects.filter(vk_id__in=sellers_for_goods).order_by('vk_id')
    sellers = sellers.annotate(counter=Count('barahlochannelgoods')).order_by('-counter')

    paginator = Paginator(sellers, 4*30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sellers/sellers_list.html', {'sellers': page_obj})


def seller_detail(request, pk):
    seller = get_object_or_404(Sellers, pk=pk)
    goods = _GOODS.objects.filter(seller_id=seller.vk_id).order_by('-date')

    city = None
    if seller.city_id:
        try:
            city = Cities.objects.get(id=seller.city_id)
        except Cities.DoesNotExist:
            city = None

    paginator = Paginator(goods, 1*30)
    channel = _CHANNEL

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sellers/seller_detail.html', {
        'seller': seller, 'goods': page_obj, 'city': city, 'channel': channel, 'pagination': True})


def cities_list(request):
    sellers_for_goods = _GOODS.objects.values('seller_id')
    cities_for_goods = Sellers.objects.filter(vk_id__in=sellers_for_goods).values('city_id')
    cities = Cities.objects.filter(id__in=cities_for_goods).order_by('id')

    return render(request, 'city/cities_list.html', {'cities': cities})


def city_page(request, pk):
    city = get_object_or_404(Cities, pk=pk)
    sellers = Sellers.objects.filter(city_id=pk)

    goods = _GOODS.objects.filter(seller_id__in=sellers).order_by('-date')
    count = goods.count

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    channel = _CHANNEL

    return render(request, 'city/city_goods.html', {
        'city': city, 'goods': page_obj, 'count': count, 'channel': channel, 'pagination': True})


def city_sellers(request, pk):
    city = get_object_or_404(Cities, pk=pk)
    sellers_for_goods = _GOODS.objects.values('seller_id')
    sellers = Sellers.objects.filter(city_id=pk, vk_id__in=sellers_for_goods)
    sellers = sellers.annotate(counter=Count('barahlochannelgoods')).order_by('-counter')

    return render(request, 'city/city_sellers.html', {'sellers': sellers, 'city': city})


def goods_list(request):
    goods = _GOODS.objects.all().order_by('-date')

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    channel = _CHANNEL

    return render(request, 'goods/goods_list.html', {'goods': page_obj, 'channel': channel})


def goods_hash(request, photo_hash):
    goods = _GOODS.objects.filter(hash=photo_hash).order_by('-date')
    channel = _CHANNEL
    return render(request, 'goods/goods_hash.html', {'goods': goods, 'channel': channel})


def goods_duplicates(request):
    hash_counter = \
        _GOODS.objects.values("hash").exclude(hash=None).annotate(counter=Count("vk_photo_id")).filter(counter__gt=2)
    hashes = [x['hash'] for x in hash_counter]

    goods = _GOODS.objects.filter(hash__in=hashes).order_by('-date')

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    channel = _CHANNEL

    return render(request, 'goods/goods_duplicates.html', {'goods': page_obj, 'channel': channel})


def good_detail(request, owner_id, photo_id):
    good = get_object_or_404(_GOODS, vk_owner_id=owner_id, vk_photo_id=photo_id)
    return render(request, 'goods/good_detail.html', {'good': good })


def albums_list(request):
    albums = _ALBUMS.objects.all().order_by('owner_id', 'album_id')

    owners = _ALBUMS.objects.values('owner_id')
    owners = [-(x['owner_id']) for x in owners]
    groups = Groups.objects.filter(id__in=owners)

    for a in albums:
        if a.owner_id < 0:
            for g in groups:
                if -a.owner_id == g.id:
                    a.owner_name = g.name
        else:
            try:
                seller = Sellers.objects.get(vk_id=a.owner_id)
            except Sellers.DoesNotExist:
                seller = None
            if seller:
                a.owner_name = seller.first_name + ' ' + seller.last_name

    return render(request, 'albums/albums_list.html', {'albums': albums, 'groups': groups})

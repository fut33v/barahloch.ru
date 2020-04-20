from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from django.db.models import Count
from .models import Sellers, BarahlochannelGoods, BarahlochannelMtbGoods, Cities, BarahlochannelAlbums, Groups


_GOODS = BarahlochannelGoods
_CHANNEL = "barahlochannel"


def sellers_list(request):
    sellers_for_goods = _GOODS.objects.values('seller_id')
    sellers = Sellers.objects.filter(vk_id__in=sellers_for_goods)
    # owners = [-(x['owner_id']) for x in owners]

    paginator = Paginator(sellers, 3*30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sellers/sellers_list.html', {'sellers': page_obj})


def seller_detail(request, pk):
    seller = get_object_or_404(Sellers, pk=pk)
    goods = _GOODS.objects.filter(seller_id=seller.vk_id).order_by('date')

    city = None
    if seller.city_id:
        city = Cities.objects.get(id=seller.city_id)

    paginator = Paginator(goods, 1*30)
    channel = _CHANNEL

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sellers/seller_detail.html', {
        'seller': seller, 'goods': page_obj, 'city': city, 'channel': channel, 'pagination': True})


def city_page(request, pk):
    city = get_object_or_404(Cities, pk=pk)
    return render(request, 'city/city.html', {'city': city})


def city_sellers(request, pk):
    city = get_object_or_404(Cities, pk=pk)
    sellers = Sellers.objects.filter(city_id=pk)
    return render(request, 'city/city_sellers.html', {'sellers': sellers, 'city': city})


def city_goods(request, pk):
    city = get_object_or_404(Cities, pk=pk)
    sellers = Sellers.objects.filter(city_id=pk)

    goods = _GOODS.objects.filter(seller_id__in=sellers).order_by('date')
    count = goods.count

    paginator = Paginator(goods, 3*30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    channel = _CHANNEL

    return render(request, 'city/city_goods.html', {
        'city': city, 'goods': page_obj, 'count': count, 'channel': channel, 'pagination': True})


def goods_hash(request, photo_hash):
    goods = _GOODS.objects.filter(hash=photo_hash)
    channel = _CHANNEL
    return render(request, 'goods/goods_hash.html', {'goods': goods, 'channel': channel})


def goods_duplicates(request):
    goods = _GOODS.objects.values('hash').order_by('date')[:2000] #.annotate(counter=Count())
    channel = _CHANNEL
    return render(request, 'goods/goods_hash.html', {'goods': goods, 'channel': channel})


def cities_list(request):
    cities = Cities.objects.all().order_by('id')
    return render(request, 'city/cities_list.html', {'cities': cities})


def albums_list(request):
    albums = BarahlochannelAlbums.objects.all().order_by('owner_id')
    owners = BarahlochannelAlbums.objects.values('owner_id')
    owners = [-(x['owner_id']) for x in owners]
    groups = Groups.objects.filter(id__in=owners)

    for a in albums:
        for g in groups:
            if -a.owner_id == g.id:
                a.group_name = g.name

    return render(request, 'albums/albums_list.html', {'albums': albums, 'groups': groups})

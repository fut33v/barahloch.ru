from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from django.db.models import Count
from .models import Sellers, BarahlochannelGoods, BarahlochannelMtbGoods, Cities


def sellers_list(request):
    sellers = Sellers.objects.all()

    paginator = Paginator(sellers, 3*30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sellers/sellers_list.html', {'sellers': page_obj})


def seller_detail(request, pk):
    seller = get_object_or_404(Sellers, pk=pk)
    fix_goods = BarahlochannelGoods.objects.filter(seller_id=seller.vk_id).order_by('date')
    mtb_goods = BarahlochannelMtbGoods.objects.filter(seller_id=seller.vk_id).order_by('date')

    city = None
    if seller.city_id:
        city = Cities.objects.get(id=seller.city_id)

    if fix_goods:
        paginator = Paginator(fix_goods, 1*30)
        channel = "barahlochannel"
    else:
        paginator = Paginator(mtb_goods, 1*30)
        channel = "barahlochannel_mtb"

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 'mtb_goods': mtb_goods,
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

    mtb = request.GET.get('mtb')
    if mtb:
        goods = BarahlochannelMtbGoods.objects.filter(seller_id__in=sellers).order_by('date')
    else:
        goods = BarahlochannelGoods.objects.filter(seller_id__in=sellers).order_by('date')
    count = goods.count

    paginator = Paginator(goods, 3*30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    channel = 'barahlochannel'

    return render(request, 'city/city_goods.html', {
        'city': city, 'goods': page_obj, 'count': count, 'channel': channel, 'pagination': True})


def goods_hash(request, photo_hash):
    goods = BarahlochannelGoods.objects.filter(hash=photo_hash)
    channel = 'barahlochannel'
    return render(request, 'goods/goods_hash.html', {'goods': goods, 'channel': channel})


def goods_duplicates(request):
    goods = BarahlochannelGoods.objects.values('hash').order_by('date')[:2000] #.annotate(counter=Count())
    # goods = BarahlochannelGoods.objects.filter(hash=photo_hash)
    channel = 'barahlochannel'
    return render(request, 'goods/goods_hash.html', {'goods': goods, 'channel': channel})


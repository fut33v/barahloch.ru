from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator

from django.conf import settings
from social_django.models import UserSocialAuth, AbstractUserSocialAuth

from barahlochannel.settings import ChannelEnum
from django.db.models import Count
from django.contrib.auth import authenticate, login, logout
from .models import Sellers, BarahlochannelGoods, BarahlochannelAlbums, Groups, Cities, TgGoods, TgSellers

from itertools import chain

_GOODS = BarahlochannelGoods
_ALBUMS = BarahlochannelAlbums

if settings.CHANNEL == ChannelEnum.FIX_SHOSSE:
    _CHANNEL = "barahlochannel"
elif settings.CHANNEL == ChannelEnum.MTB:
    _CHANNEL = "barahlochannel_mtb"
elif settings.CHANNEL == ChannelEnum.DEBUG:
    _CHANNEL = "barahl0"


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
    tg_goods = TgGoods.objects.all().order_by('-date')

    goods = list(chain(tg_goods, goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    channel = _CHANNEL
    vk_user_id = None
    if request.user.is_authenticated:
        user = request.user
        try:
            vk_user_id = int(user.social_auth.get(provider='vk-oauth2').uid)
        except UserSocialAuth.DoesNotExist:
            vk_user_id = None

    return render(request, 'goods/goods_list.html', {
        'goods': page_obj,
        'channel': channel,
        'vk_user_id': vk_user_id})


def goods_hash(request, photo_hash):
    goods = _GOODS.objects.filter(hash=photo_hash).order_by('-date')
    channel = _CHANNEL
    return render(request, 'goods/goods_hash.html', {'goods': goods, 'channel': channel})


def goods_duplicates(request):
    hash_counter = \
        _GOODS.objects.values("hash").exclude(hash=None).annotate(counter=Count("vk_photo_id")).filter(counter__gt=1)
    hashes = [x['hash'] for x in hash_counter]

    goods_tmp = _GOODS.objects.filter(hash__in=hashes).order_by('-date')
    goods = []
    hash_set = set()
    for g in goods_tmp:
        if g.hash not in hash_set:
            hash_set.add(g.hash)
            goods.append(g)

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    channel = _CHANNEL

    return render(request, 'goods/goods_duplicates.html', {'goods': page_obj, 'channel': channel})


def good_detail(request, owner_id, photo_id):
    good = get_object_or_404(_GOODS, vk_owner_id=owner_id, vk_photo_id=photo_id)
    channel = _CHANNEL
    return render(request, 'goods/good_detail.html', {'good': good, 'channel': channel})


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


def telegram_goods_list(request):
    goods = TgGoods.objects.all().order_by('-date')

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    channel = _CHANNEL

    return render(request, 'telegram/goods_list.html', {'goods': page_obj, 'channel': channel})


def telegram_good_detail(request, tg_post_id):
    good = get_object_or_404(TgGoods, tg_post_id=tg_post_id)
    channel = _CHANNEL
    return render(request, 'telegram/good_detail.html', {'good': good, 'channel': channel})


def telegram_goods_category(request, category):
    goods = TgGoods.objects.filter(category=category).order_by('-date')

    paginator = Paginator(goods, 11 * 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    channel = _CHANNEL

    return render(request, 'telegram/goods_list.html', {'goods': page_obj, 'channel': channel})


def telegram_seller_detail(request, tg_user_id):
    seller = get_object_or_404(TgSellers, pk=tg_user_id)
    goods = TgGoods.objects.filter(tg_user_id=seller.tg_user_id).order_by('-date')

    paginator = Paginator(goods, 1*30)
    channel = _CHANNEL

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'telegram/seller_detail.html', {
        'seller': seller, 'goods': page_obj, 'channel': channel, 'pagination': True})


def login_view(request):
    if 'login' in request.GET and 'password' in request.GET:
        username = request.GET['login']
        password = request.GET['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'failed': True})
    else:
        return render(request, 'login.html', {})


def logout_view(request):
    logout(request)
    return redirect('/')


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('/')
    user = request.user
    try:
        vk_user_id = int(user.social_auth.get(provider='vk-oauth2').uid)
    except UserSocialAuth.DoesNotExist:
        vk_user_id = None

    vk_seller = None
    if vk_user_id:
        try:
            vk_seller = Sellers.objects.get(vk_id=vk_user_id)
        except Sellers.DoesNotExist:
            vk_seller = None

    tg_seller = None
    tg_username = None
    try:
        tg_user_id = int(user.social_auth.get(provider='telegram').uid)
        extra_data = user.social_auth.get(provider='telegram').extra_data
        if 'username' in extra_data:
            if len(extra_data['username']) != 0:
                tg_username = extra_data['username'][0]
    except UserSocialAuth.DoesNotExist:
        tg_user_id = None
    if tg_user_id:
        try:
            tg_seller = TgSellers.objects.get(tg_user_id=tg_user_id)
        except TgSellers.DoesNotExist:
            tg_seller = None

    tg_goods = TgGoods.objects.filter(tg_user_id=tg_user_id).order_by('-date')
    vk_goods = BarahlochannelGoods.objects.filter(seller_id=vk_user_id).order_by('-date')

    goods = list(chain(tg_goods, vk_goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    # get goods for this profile
    # and pagination
    paginator = Paginator(goods, 15*2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'profile.html', {
        'vk_user_id': vk_user_id,
        'tg_user_id': tg_user_id,
        'tg_username': tg_username,
        'vk_seller': vk_seller,
        'tg_seller': tg_seller,
        'goods': page_obj,
        'channel': _CHANNEL
    })

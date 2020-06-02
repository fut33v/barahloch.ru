from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator

from django.conf import settings
from social_django.models import UserSocialAuth, AbstractUserSocialAuth

from barahlochannel.settings import ChannelEnum
from django.db.models import Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test

from . import context_processors
from .models import Sellers, VkGoods, BarahlochannelAlbums, Groups, Cities, TgGoods, TgSellers, ProductStateEnum

from itertools import chain

_GOODS = VkGoods
_ALBUMS = BarahlochannelAlbums

if settings.CHANNEL == ChannelEnum.FIX:
    _CHANNEL = "barahlochannel"
elif settings.CHANNEL == ChannelEnum.MTB:
    _CHANNEL = "barahlochannel_mtb"
elif settings.CHANNEL == ChannelEnum.DEBUG:
    _CHANNEL = "barahl0"


def process_product_buttons(request):
    if not request.POST:
        return

    product_type = request.POST.get('type', None)
    if not product_type:
        return

    product = None

    if product_type == 'telegram':
        product_id = request.POST.get('id', None)
        if not product_id:
            return
        try:
            product = TgGoods.objects.get(tg_post_id=product_id)
        except TgGoods.DoesNotExist:
            product = None

    elif product_type == 'vkontakte':
        product_id = request.POST.get('id', None)
        if not product_id:
            return
        ow_ph_id = product_id.split('_')
        if len(ow_ph_id) != 2:
            return
        owner_id = ow_ph_id[0]
        photo_id = ow_ph_id[1]
        try:
            product = VkGoods.objects.get(vk_owner_id=owner_id, vk_photo_id=photo_id)
        except VkGoods.DoesNotExist:
            product = None

    if not product:
        return

    products = None
    if isinstance(product, VkGoods):
        products = VkGoods.objects.filter(hash=product.hash)
    elif isinstance(product, TgGoods):
        products = TgGoods.objects.filter(hash=product.hash)

    if not products:
        return

    action = request.POST.get('action', None)
    state = None
    if action:
        if action == 'sold':
            state = ProductStateEnum.SOLD.name
        elif action == 'up':
            ...
        elif action == 'back':
            state = ProductStateEnum.SHOW.name
        elif action == 'delete':
            state = ProductStateEnum.HIDDEN.name

    if not state:
        return

    for p in products:
        p.state = state
        p.save()
    # product.save()


def process_product_buttons_decorator(func):
    def wrapper(*args, **kwargs):
        request = args[0]
        if request.POST:
            process_product_buttons(request)
        return func(*args, **kwargs)
    return wrapper


def sellers_list(request):
    sellers_for_goods = _GOODS.objects.values('seller_id')

    sellers = Sellers.objects.filter(vk_id__in=sellers_for_goods).order_by('vk_id')
    sellers = sellers.annotate(counter=Count('vkgoods')).order_by('-counter')

    paginator = Paginator(sellers, 4*30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vkontakte/sellers_list.html', {'sellers': page_obj})


@process_product_buttons_decorator
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

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vkontakte/seller_detail.html', {
        'seller': seller, 'goods': page_obj, 'city': city, 'pagination': True})


def cities_list(request):
    sellers_for_goods = _GOODS.objects.values('seller_id')
    cities_for_goods = Sellers.objects.filter(vk_id__in=sellers_for_goods).values('city_id')
    cities = Cities.objects.filter(id__in=cities_for_goods).order_by('id')

    return render(request, 'city/cities_list.html', {'cities': cities})


@process_product_buttons_decorator
def city_page(request, pk):
    city = get_object_or_404(Cities, pk=pk)
    sellers = Sellers.objects.filter(city_id=pk)

    goods = _GOODS.objects.filter(seller_id__in=sellers).order_by('-date')
    count = goods.count

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'city/city_goods.html', {
        'city': city, 'goods': page_obj, 'count': count, 'pagination': True})


def city_sellers(request, pk):
    city = get_object_or_404(Cities, pk=pk)
    sellers_for_goods = _GOODS.objects.values('seller_id')
    sellers = Sellers.objects.filter(city_id=pk, vk_id__in=sellers_for_goods)
    sellers = sellers.annotate(counter=Count('vkgoods')).order_by('-counter')

    return render(request, 'city/city_sellers.html', {'sellers': sellers, 'city': city})


@process_product_buttons_decorator
def goods_list(request):
    vk_goods = _GOODS.objects.exclude(state='HIDDEN').order_by('-date')
    tg_goods = TgGoods.objects.exclude(state='HIDDEN').order_by('-date')

    goods = list(chain(tg_goods, vk_goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'goods_list.html', {
        'goods': page_obj
        })


@process_product_buttons_decorator
def goods_hash(request, photo_hash):
    goods = _GOODS.objects.filter(hash=photo_hash).order_by('-date')
    return render(request, 'goods_hash.html', {'goods': goods})


@process_product_buttons_decorator
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

    return render(request, 'goods_duplicates.html', {'goods': page_obj})


def good_detail(request, owner_id, photo_id):
    good = get_object_or_404(_GOODS, vk_owner_id=owner_id, vk_photo_id=photo_id)
    return render(request, 'vkontakte/good_detail.html', {'good': good})


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


@process_product_buttons_decorator
def telegram_goods_list(request):
    goods = TgGoods.objects.all().order_by('-date')

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'telegram/goods_list.html', {'goods': page_obj})


def telegram_good_detail(request, tg_post_id):
    good = get_object_or_404(TgGoods, tg_post_id=tg_post_id)
    return render(request, 'telegram/good_detail.html', {'good': good})


@process_product_buttons_decorator
def telegram_goods_category(request, category):
    goods = TgGoods.objects.filter(category=category).order_by('-date')

    paginator = Paginator(goods, 11 * 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'telegram/goods_list.html', {'goods': page_obj})


@process_product_buttons_decorator
def telegram_seller_detail(request, tg_user_id):
    seller = get_object_or_404(TgSellers, pk=tg_user_id)
    goods = TgGoods.objects.filter(tg_user_id=seller.tg_user_id).order_by('-date')

    paginator = Paginator(goods, 1*30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'telegram/seller_detail.html', {
        'seller': seller, 'goods': page_obj, 'pagination': True})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile_view')

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


@login_required
def profile_view(request):
    if request.POST:
        process_product_buttons(request)

    sellers = context_processors.sellers(request)

    vk_user_id = sellers.get('vk_user_id', None)
    tg_user_id = sellers.get('tg_user_id', None)

    tg_goods = []
    vk_goods = []

    if tg_user_id:
        tg_goods = TgGoods.objects.filter(tg_user_id=tg_user_id).order_by('-date')
    if vk_user_id:
        vk_goods = VkGoods.objects.filter(seller_id=vk_user_id).order_by('-date')

    goods = list(chain(tg_goods, vk_goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    paginator = Paginator(goods, 15*2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'profile.html', {
        'goods': page_obj
    })


@user_passes_test(lambda u: u.is_superuser)
def admin_view(request):
    # get users
    users = User.objects.all()

    for user in users:
        try:
            user_vk = user.social_auth.get(provider='vk-oauth2')
        except UserSocialAuth.DoesNotExist:
            user_vk = None
        user.user_vk = user_vk

        try:
            user_tg = user.social_auth.get(provider='telegram')
        except UserSocialAuth.DoesNotExist:
            user_tg = None
        if user_tg:
            extra_data = user_tg.extra_data
            if 'username' in extra_data:
                if len(extra_data['username']) != 0:
                    tg_username = extra_data['username'][0]
                    user_tg.username = tg_username
        user.user_tg = user_tg

    return render(request, 'admin/admin.html', {'users': users})


@user_passes_test(lambda u: u.is_superuser)
@process_product_buttons_decorator
def admin_hidden_goods(request):

    vk_goods = VkGoods.objects.filter(state='HIDDEN').order_by('-date')
    tg_goods = TgGoods.objects.filter(state='HIDDEN').order_by('-date')

    goods = list(chain(tg_goods, vk_goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/hidden_goods.html', {'goods': page_obj})

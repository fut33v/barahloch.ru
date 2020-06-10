from itertools import chain

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect

from social_django.models import UserSocialAuth

from . import context_processors
from .models import VkSellers, VkGoods, Albums, Groups, Cities, TgGoods, TgSellers, ProductStateEnum
from .serializers import VkSellersSerializer, VkGoodsSerializer, AlbumsSerializer, CitiesSerializer, TgSellersSerializer, TgGoodsSerializer
from rest_framework.authtoken.models import Token
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.decorators import action
from rest_framework.response import Response


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

    button_action = request.POST.get('action', None)
    state = None
    if button_action:
        if button_action == 'sold':
            state = ProductStateEnum.SOLD.name
        elif button_action == 'up':
            ...
        elif button_action == 'back':
            state = ProductStateEnum.SHOW.name
        elif button_action == 'delete':
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


def get_city_goods(city_id):
    vk_sellers = VkSellers.objects.filter(city_id=city_id)
    tg_sellers = TgSellers.objects.filter(city_id=city_id)

    vk_goods = VkGoods.objects.filter(seller_id__in=vk_sellers, state='SHOW').order_by('-date')
    tg_goods = TgGoods.objects.filter(tg_user_id__in=tg_sellers, state='SHOW').order_by('-date')

    goods = list(chain(tg_goods, vk_goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    return goods


def get_city_sellers(city_id):
    sellers_for_goods = VkGoods.objects.values('seller_id')
    vk_sellers = VkSellers.objects.filter(city_id=city_id, vk_id__in=sellers_for_goods)
    vk_sellers = vk_sellers.annotate(counter=Count('vkgoods')).order_by('-counter')

    tg_sellers = TgSellers.objects.filter(city_id=city_id)
    tg_sellers = tg_sellers.annotate(counter=Count('tggoods')).order_by('-counter')

    sellers = list(chain(tg_sellers, vk_sellers))

    return sellers


def get_user_goods(request):
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

    return goods


def get_all_seller_goods(vk_user_id=None, tg_user_id=None):
    if not vk_user_id and not tg_user_id:
        return None

    vk_goods = []
    tg_goods = []

    if vk_user_id:
        vk_goods = VkGoods.objects.filter(seller_id=vk_user_id).order_by('-date')
        try:
            vk_user = UserSocialAuth.objects.get(provider='vk-oauth2', uid=vk_user_id)
        except UserSocialAuth.DoesNotExist:
            vk_user = None
        if vk_user:
            try:
                tg_user = vk_user.user.social_auth.get(provider='telegram')
            except UserSocialAuth.DoesNotExist:
                tg_user = None
            if tg_user:
                tg_goods = TgGoods.objects.filter(tg_user_id=tg_user.uid).order_by('-date')

    elif tg_user_id:
        tg_goods = TgGoods.objects.filter(tg_user_id=tg_user_id).order_by('-date')
        try:
            tg_user = UserSocialAuth.objects.get(provider='telegram', uid=tg_user_id)
        except UserSocialAuth.DoesNotExist:
            tg_user = None
        if tg_user:
            try:
                vk_user = tg_user.user.social_auth.get(provider='vk-oauth2')
            except UserSocialAuth.DoesNotExist:
                vk_user = None
            if vk_user:
                vk_goods = VkGoods.objects.filter(seller_id=vk_user.uid).order_by('-date')

    goods = list(chain(tg_goods, vk_goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    return goods


def sellers_list(request):
    sellers_for_goods = VkGoods.objects.values('seller_id')

    vk_sellers = VkSellers.objects.filter(vk_id__in=sellers_for_goods).order_by('vk_id')
    vk_sellers = vk_sellers.annotate(counter=Count('vkgoods')).order_by('-counter')

    tg_sellers = TgSellers.objects.all().annotate(counter=Count('tggoods')).order_by('-counter')

    sellers = list(chain(tg_sellers, vk_sellers))

    paginator = Paginator(sellers, 4*30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vkontakte/sellers_list.html', {'sellers': page_obj})


@process_product_buttons_decorator
def seller_detail(request, pk):
    seller = get_object_or_404(VkSellers, pk=pk)

    goods = get_all_seller_goods(vk_user_id=seller.vk_id)

    paginator = Paginator(goods, 1*30)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vkontakte/seller_detail.html', {
        'seller': seller, 'goods': page_obj, 'pagination': True})


def cities_list(request):
    sellers_for_goods = VkGoods.objects.values('seller_id')
    cities_for_goods = VkSellers.objects.filter(vk_id__in=sellers_for_goods).values('city_id')
    cities = Cities.objects.filter(id__in=cities_for_goods).order_by('id')

    return render(request, 'city/cities_list.html', {'cities': cities})


@process_product_buttons_decorator
def city_page(request, pk):
    city = get_object_or_404(Cities, pk=pk)

    goods = get_city_goods(pk)

    count = goods.count

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'city/city_goods.html', {
        'city': city, 'goods': page_obj, 'count': count, 'pagination': True})


def city_sellers(request, pk):
    city = get_object_or_404(Cities, pk=pk)

    sellers = get_city_sellers(pk)

    return render(request, 'city/city_sellers.html', {'sellers': sellers, 'city': city})


@process_product_buttons_decorator
def goods_list(request):
    vk_goods = VkGoods.objects.filter(state='SHOW').order_by('-date')
    tg_goods = TgGoods.objects.filter(state='SHOW').order_by('-date')

    goods = list(chain(tg_goods, vk_goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'goods/goods_list.html', {
        'goods': page_obj
        })


@process_product_buttons_decorator
def goods_hash(request, photo_hash):
    vk_goods = VkGoods.objects.filter(hash=photo_hash).order_by('-date')
    tg_goods = TgGoods.objects.filter(hash=photo_hash).order_by('-date')

    goods = list(chain(tg_goods, vk_goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    return render(request, 'goods/goods_hash.html', {'goods': goods})


@process_product_buttons_decorator
def goods_duplicates(request):
    actual_goods = VkGoods.objects.filter(state='SHOW')
    hash_counter = \
        actual_goods.values("hash").exclude(hash=None).annotate(counter=Count("vk_photo_id")).filter(counter__gt=1)
    hashes = [x['hash'] for x in hash_counter]

    goods_tmp = actual_goods.filter(hash__in=hashes).order_by('-date')
    goods = []
    hash_set = set()
    for g in goods_tmp:
        if g.hash not in hash_set:
            hash_set.add(g.hash)
            goods.append(g)

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for x in page_obj.object_list:
        print(x.vk_owner_id, x.vk_photo_id, x.hash)
    return render(request, 'goods/goods_duplicates.html', {'goods': page_obj})


def good_detail(request, owner_id, photo_id):
    good = get_object_or_404(VkGoods, vk_owner_id=owner_id, vk_photo_id=photo_id)
    return render(request, 'vkontakte/good_detail.html', {'good': good})


def albums_list(request):
    albums = Albums.objects.all().order_by('owner_id', 'album_id')

    owners = Albums.objects.values('owner_id')
    owners = [-(x['owner_id']) for x in owners]
    groups = Groups.objects.filter(id__in=owners)

    for a in albums:
        if a.owner_id < 0:
            for g in groups:
                if -a.owner_id == g.id:
                    a.owner_name = g.name
        else:
            try:
                seller = VkSellers.objects.get(vk_id=a.owner_id)
            except VkSellers.DoesNotExist:
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

    goods = get_all_seller_goods(tg_user_id=seller.tg_user_id)

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

    goods = get_user_goods(request)
    token = Token.objects.get(user=request.user)

    paginator = Paginator(goods, 15*2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'profile.html', {
        'goods': page_obj,
        'token': token
    })


@user_passes_test(lambda u: u.is_superuser)
def admin_view(request):
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

        if user_vk:
            try:
                seller_vk = VkSellers.objects.get(vk_id=user_vk.uid)
            except VkSellers.DoesNotExist:
                seller_vk = None
            user.seller_vk = seller_vk

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


@user_passes_test(lambda u: u.is_superuser)
@process_product_buttons_decorator
def admin_sold_goods(request):

    vk_goods = VkGoods.objects.filter(state='SOLD').order_by('-date')
    tg_goods = TgGoods.objects.filter(state='SOLD').order_by('-date')

    goods = list(chain(tg_goods, vk_goods))
    goods.sort(key=lambda g: g.date, reverse=True)

    paginator = Paginator(goods, 11*3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/hidden_goods.html', {'goods': page_obj})


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class ReadAnyWriteAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        elif request.user.is_staff:
            return True
        return False


class VkSellerViewSet(viewsets.ModelViewSet):
    """
    Продавцы из ВКонтакте.
    """
    permission_classes = [ReadAnyWriteAdmin]
    queryset = VkSellers.objects.annotate(counter=Count('vkgoods')).order_by('-counter')
    serializer_class = VkSellersSerializer

    @action(methods=['get'], detail=True, permission_classes=[ReadOnly], url_path='goods', url_name='seller_goods')
    def goods(self, request, pk=None):
        queryset = VkGoods.objects.filter(seller_id=pk).order_by('-date')
        serializer_context = {
            'request': request,
        }
        serializer = VkGoodsSerializer(queryset, many=True, context=serializer_context)
        return Response(serializer.data)


class TgSellersViewSet(viewsets.ModelViewSet):
    """
    Продавцы из Telegram.
    """
    permission_classes = [ReadAnyWriteAdmin]
    queryset = TgSellers.objects.annotate(counter=Count('tggoods')).order_by('-counter')
    serializer_class = TgSellersSerializer

    @action(methods=['get'], detail=True, permission_classes=[ReadOnly], url_path='goods', url_name='seller_goods')
    def goods(self, request, pk=None):
        queryset = TgGoods.objects.filter(tg_user_id=pk).order_by('-date')
        serializer_context = {
            'request': request,
        }
        serializer = TgGoodsSerializer(queryset, many=True, context=serializer_context)
        return Response(serializer.data)


class VkGoodsViewSet(viewsets.ModelViewSet):
    """
    Товары из ВК.
    """
    permission_classes = [ReadAnyWriteAdmin]
    queryset = VkGoods.objects.exclude(state='HIDDEN').order_by('-date')
    serializer_class = VkGoodsSerializer


class TgGoodsViewSet(viewsets.ModelViewSet):
    """
    Товары из Telegram.
    """
    permission_classes = [ReadAnyWriteAdmin]
    queryset = TgGoods.objects.exclude(state='HIDDEN').order_by('-date')
    serializer_class = TgGoodsSerializer


class AlbumsViewSet(viewsets.ModelViewSet):
    """
    Список используемых каналом альбомов ВК.
    """
    permission_classes = [ReadAnyWriteAdmin]
    queryset = Albums.objects.order_by('-owner_id')
    serializer_class = AlbumsSerializer


class CitiesViewSet(viewsets.ModelViewSet):
    """
    Список городов.
    """
    permission_classes = [ReadAnyWriteAdmin]
    queryset = Cities.objects.order_by('id')
    serializer_class = CitiesSerializer

    @action(methods=['get'], detail=True, permission_classes=[ReadOnly], url_path='goods', url_name='seller_goods')
    def goods(self, request, pk=None):
        city_goods = get_city_goods(pk)
        serializer_context = {
            'request': request,
        }
        serializer = TgGoodsSerializer(city_goods, many=True, context=serializer_context)
        return Response(serializer.data)

    @action(methods=['get'], detail=True, permission_classes=[ReadOnly], url_path='vk-sellers', url_name='city_vk_sellers')
    def vk_sellers(self, request, pk=None):
        sellers_for_goods = VkGoods.objects.values('seller_id')
        vk_sellers = VkSellers.objects.filter(city_id=pk, vk_id__in=sellers_for_goods)
        vk_sellers = vk_sellers.annotate(counter=Count('vkgoods')).order_by('-counter')
        serializer_context = {
            'request': request,
        }
        serializer = VkSellersSerializer(vk_sellers, many=True, context=serializer_context)
        return Response(serializer.data)

    @action(methods=['get'], detail=True, permission_classes=[ReadOnly], url_path='tg-sellers', url_name='city_tg_sellers')
    def tg_sellers(self, request, pk=None):
        tg_sellers = TgSellers.objects.filter(city_id=pk)
        tg_sellers = tg_sellers.annotate(counter=Count('tggoods')).order_by('-counter')
        serializer_context = {
            'request': request,
        }
        serializer = TgSellersSerializer(tg_sellers, many=True, context=serializer_context)
        return Response(serializer.data)


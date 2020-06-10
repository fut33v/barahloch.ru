from .models import VkSellers, VkGoods, Albums, Cities, TgSellers, TgGoods
from rest_framework import serializers


class VkSellersSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VkSellers
        fields = ['url', 'vk_id', 'first_name', 'last_name', 'photo', 'city_id']


class TgSellersSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TgSellers
        fields = ['url', 'tg_user_id', 'full_name', 'username', 'city_id']


class AlbumsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Albums
        fields = ['url', 'owner_id', 'album_id', 'title', 'description', 'photo']


class CitiesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Cities
        fields = ['url', 'id', 'title']


class VkGoodsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VkGoods
        fields = ['url', 'seller_id', 'tg_post_id', 'vk_owner_id', 'vk_photo_id', 'vk_album_id',
                  'descr', 'comments',
                  'hash', 'date', 'state', 'photo_link', 'photo_preview']


class TgGoodsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TgGoods
        fields = ['url', 'tg_user_id', 'tg_post_id',
                  'caption', 'descr',
                  'hash', 'date', 'state', 'photo_link', 'price', 'currency', 'category', 'ship']


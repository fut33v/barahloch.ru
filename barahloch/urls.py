from django.urls import path, register_converter
from . import views, converters

register_converter(converters.NegativeIntConverter, 'negint')


urlpatterns = [
    path('', views.goods_list, name='goods_list'),
    path('sellers', views.sellers_list, name='sellers_list'),

    path('seller/<negint:pk>/', views.seller_detail, name='seller_detail'),
    path('city/<int:pk>/', views.city_page, name='city_page'),
    path('city/<int:pk>/sellers/', views.city_sellers, name='city_sellers'),
    path('cities', views.cities_list, name='cities_list'),

    path('goods/hash/<slug:photo_hash>', views.goods_hash, name='goods_hash'),
    path('goods/duplicates', views.goods_duplicates, name='goods_duplicates'),

    path('albums', views.albums_list, name='albums_list'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.sellers_list, name='sellers_list'),
    path('seller/<int:pk>/', views.seller_detail, name='seller_detail'),
    path('city/<int:pk>/', views.city_page, name='city_page'),
    path('city/<int:pk>/sellers/', views.city_sellers, name='city_sellers'),
    path('city/<int:pk>/goods/', views.city_goods, name='city_goods'),
    path('goods/hash/<slug:photo_hash>', views.goods_hash, name='goods_hash'),
    path('goods/duplicates', views.goods_duplicates, name='goods_duplicates'),
]

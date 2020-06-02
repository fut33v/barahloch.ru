from django.urls import path, register_converter, include
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
    path('goods/<negint:owner_id>_<int:photo_id>', views.good_detail, name='good_detail'),

    path('tg_goods/<int:tg_post_id>', views.telegram_good_detail, name='telegram_good_detail'),
    path('tg_goods/category/<slug:category>', views.telegram_goods_category, name='telegram_goods_category'),
    path('tg_seller/<int:tg_user_id>/', views.telegram_seller_detail, name='telegram_seller_detail'),

    path('profile', views.profile_view, name='profile_view'),

    path('albums', views.albums_list, name='albums_list'),

    path('login', views.login_view, name='login_view'),
    path('logout', views.logout_view, name='logout_view'),

    path('adminka', views.admin_view, name='admin_view'),
    path('adminka/hidden_goods', views.admin_hidden_goods, name='admin_hidden_goods'),

    path('', include('social_django.urls')),

]

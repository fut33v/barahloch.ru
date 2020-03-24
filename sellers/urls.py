from django.urls import path
from . import views

urlpatterns = [
    path('', views.sellers_list, name='sellers_list'),
    path('seller/<int:pk>/', views.seller_detail, name='seller_detail'),
]

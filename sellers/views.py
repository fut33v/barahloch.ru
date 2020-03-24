from django.shortcuts import render, get_object_or_404
from .models import Sellers, Goods


def sellers_list(request):
    # sellers = Sellers.objects.filter(city='Великий Новгород')
    sellers = Sellers.objects.all()
    return render(request, 'sellers/sellers_list.html', {'sellers': sellers})


def seller_detail(request, pk):
    seller = get_object_or_404(Sellers, pk=pk)
    goods = Goods.objects.filter(seller_id=seller.vk_id)
    return render(request, 'sellers/seller_detail.html', {'seller': seller, 'goods': goods})

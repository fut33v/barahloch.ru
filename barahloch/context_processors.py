from social_django.models import UserSocialAuth

from barahloch.models import VkSellers, TgSellers
from barahlochannel.settings import DOMAIN, TELEGRAM_BOT_NAME, CHANNEL_NAME


def domain(request):
    return {'domain': DOMAIN}


def telegram_bot_name(request):
    return {'telegram_bot_name': TELEGRAM_BOT_NAME,
            'channel': CHANNEL_NAME}


def sellers(request):
    if not request.user.is_authenticated:
        return {}
    user = request.user
    try:
        vk_user_id = int(user.social_auth.get(provider='vk-oauth2').uid)
    except UserSocialAuth.DoesNotExist:
        vk_user_id = None

    vk_seller = None
    if vk_user_id:
        try:
            vk_seller = VkSellers.objects.get(vk_id=vk_user_id)
        except VkSellers.DoesNotExist:
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

    return {
        'vk_user_id': vk_user_id,
        'vk_seller': vk_seller,
        'tg_user_id': tg_user_id,
        'tg_username': tg_username,
        'tg_seller': tg_seller
    }

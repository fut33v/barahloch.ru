import os

import telegram.ext
import telegram.error

from barahl0bot.bullshit.vkontakte import VkontakteInfoGetter
from barahl0bot.bullshit.database import PostgreBarahlochDatabase
from barahl0bot.bullshit.structures import Product
from barahl0bot.bullshit.settings import Barahl0botSettings


class BarahlochTasksLogic:
    _settings: Barahl0botSettings
    _vk_getter: VkontakteInfoGetter
    _database: PostgreBarahlochDatabase
    _telegram_bot: telegram.Bot

    @staticmethod
    def init(settings_filename: str):
        if not os.path.exists(settings_filename):
            return
        # global _VK_GETTER, _SETTINGS, _DATABASE, _TELEGRAM_BOT
        BarahlochTasksLogic._settings = Barahl0botSettings(settings_filename)
        settings = BarahlochTasksLogic._settings
        BarahlochTasksLogic._vk_getter = VkontakteInfoGetter(settings.token_vk)
        BarahlochTasksLogic._database = PostgreBarahlochDatabase(settings.channel)
        BarahlochTasksLogic._telegram_bot = telegram.Bot(token=settings.token_telegram)

    @staticmethod
    def update_good_telegram(owner_id: int, photo_id: int):
        # get product from database
        product = BarahlochTasksLogic._database.get_product_by_owner_photo_id(owner_id=owner_id, photo_id=photo_id)
        if not Product:
            return
        try:
            settings = BarahlochTasksLogic._settings
            result = BarahlochTasksLogic._telegram_bot.edit_message_text(
                chat_id='@' + settings.channel,
                message_id=product.tg_post_id,
                text=product.build_message_telegram(channel=settings.channel, website=settings.website, from_db=True),
                parse_mode=telegram.ParseMode.HTML
            )
            return result
        except telegram.error.TelegramError as te:
            # _LOGGER.warning(te)
            return te.message

    @staticmethod
    def get_goods_show_ids(filter_days_down_limit, filter_days_up_limit):
        return BarahlochTasksLogic._database.get_goods_with_state_show_ids(
            filter_days_down_limit=filter_days_down_limit, filter_days_up_limit=filter_days_up_limit)

    @staticmethod
    def check_is_sold(owner_id: int, photo_id: int):
        return BarahlochTasksLogic._vk_getter.check_is_sold(owner_id, photo_id)

    @staticmethod
    def set_good_sold(owner_id: int, photo_id: int):
        BarahlochTasksLogic._database.set_good_sold(owner_id, photo_id)


import vk_api
import random
import requests
import bs4
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from datetime import datetime
import time
from threading import Timer, Thread
from bs4 import BeautifulSoup
from favorite_item import *


class CsBot:
    def __init__(self, token):
        self.token = token
        self.vk_session = vk_api.VkApi(token=self.token)
        self.long_poll = VkLongPoll(self.vk_session)

        self.keyboard = VkKeyboard(one_time=False)
        self.keyboard.add_button('Избранное⭐', color=VkKeyboardColor.SECONDARY)
        self.keyboard.add_line()
        self.keyboard.add_button('Удалить🗑', color=VkKeyboardColor.NEGATIVE)
        self.keyboard.add_button('Уведомления⏰', color=VkKeyboardColor.PRIMARY)

        self.meetings = ["привет", "хай", "шалом", "вечер в хату", "hello"]
        self.all_users = get_all_users()

        self.item_names = get_items_info(get_all_favorite_items())

    def start(self):
        print("Bot is started")

        is_deleting = False

        mailer = Thread(target=self.mailer)
        mailer.start()
        self.mail_keyboard()
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text
                    user_id = event.user_id

                    print("I get a message:", request)

                    if is_deleting and request.isdigit():
                        self._delete_favorite(user_id, int(request))
                        is_deleting = False
                    elif request.lower() in self.meetings:
                        self._write_msg(user_id, "Шалом")
                    elif request.lower() == "!удалить" or request.lower() == "удалить" or request == "Удалить🗑":
                        is_deleting = self._delete_request(user_id)
                    elif request.lower() == "!избранное" or request.lower() == "избранное" or request == "Избранное⭐":
                        self._send_favorites(user_id)
                    elif request == "Уведомления⏰":
                        self._write_msg(user_id, "Мне настолько похуй, что пока это не работает")
                    elif "steamcommunity.com/market/listings/" in request:
                        self._add_favorites(user_id, request)
                    else:
                        self._write_msg(user_id, "Ты можешь:\n"
                                                 "прислать ссылку - добавить предмет в избранное\n"
                                                 "!Избранное - получить информацию о избранных предметах\n"
                                                 "!Удалить - удалить предмет из избранного")

    def _send_keyboard(self, user_id):
        self.vk_session.method('messages.send',
                               {'user_id': user_id, 'message': None, "random_id": self.get_random_id(),
                                'keyboard': self.keyboard.get_keyboard()})

    def mail_keyboard(self):
        for user in self.all_users:
            self._send_keyboard(user)

    def mailer(self):
        while True:
            self._mail_all()
            time.sleep(5 * 60 * 60)

    def _mail_all(self):
        for user in self.all_users:
            self._send_favorites(user)

    def _delete_request(self, user_id):
        items = get_favorite_names(user_id, self.item_names)

        is_deleting = True
        if items:
            message = "Пришли цифру того, что хочешь удалить:\n"

            i = 1
            for item in items:
                message += str(i) + ': ' + item["name"] + '\n\n'
                i += 1
        else:
            message = "Пока у тебя нет избранных, однако ты " \
                      "можешь их добавить прислав мне ссылку на предмет со steamcommunity.com/market/listings/730"
            is_deleting = False

        self._write_msg(user_id, message)
        return is_deleting

    def _delete_favorite(self, user_id, number):
        if forgot_favorite(user_id, number) == -1:
            message = "Я не могу удалить предмет с таким номером"
            self._write_msg(user_id, message)
        else:
            message = "Предмет успешно удален"
            self._write_msg(user_id, message)

    def _write_msg(self, user_id, message):
        print(message, "to", user_id, "was sent")
        self.vk_session.method('messages.send',
                               {'user_id': user_id, 'message': message, "random_id": self.get_random_id(),
                                'keyboard': self.keyboard.get_keyboard()})

    def _add_favorites(self, user_id, url):

        if add_favorite_item(user_id, url) == -1:
            message = "Этот предмет уже в избранном"
        else:
            message = "Предмет добавлен!\nТеперь ты будешь получать информацию о нем!"
            item = item_from_url(url)
            steam_link = "https://steamcommunity.com/market/priceoverview/?currency=5&appid=730&market_hash_name=" + item
            prise_fee = requests.get(steam_link).json()["lowest_price"]

            self.item_names[item] = [get_item_name(item), prise_fee]

        self._write_msg(user_id, message)

    def _send_favorites(self, user_id):
        items = get_favorite_names(user_id, self.item_names)

        if items:
            message = "Твоё избранное:\n"

            for item in items:
                old_price = self.item_names[item["item_id"]][1]
                message += ' ' + item["name"] + ':\n' + item["price_fee"]
                if item["price_fee"] > old_price:
                    message += ' (+' + str(round(
                        self.price_to_float(item["price_fee"]) - self.price_to_float(old_price), 2)) + ')'
                elif item["price_fee"] < old_price:
                    message += ' (-' + str(round(
                        self.price_to_float(item["price_fee"]) - self.price_to_float(old_price), 2)) + ')'
                else:
                    message += ' (=0)'

                message += '\n\n'
        else:
            message = "Пока у тебя нет избранных, однако ты " \
                      "можешь их добавить прислав мне ссылку на предмет со steamcommunity.com/market/listings/730"

        self._write_msg(user_id, message)
        pass

    @staticmethod
    def format_text(str):
        result = ""
        for i in range(0, len(str)):
            if str[i] != '\n':
                result += str[i]
        return result

    def _send_keyboard(self, user_id):
        # print("keyboard to", user_id, "was sent")
        # self.vk_session.method('messages.send',
        #                        {"user_id": user_id,
        #                         "random_id": self.get_random_id(),
        #                         "keyboard": self.keyboard.get_keyboard(),
        #                         "message": 'Держи'})
        pass

    def _get_user_by_id(self, user_id):
        request = requests.get("https://vk.com/id" + str(user_id))
        bs = bs4.BeautifulSoup(request.text, "html.parser")

        user_name = self._clean_all_tag_from_str(bs.findAll("title")[0])

        return user_name.split()[0] + ' ' + user_name.split()[1]

    @staticmethod
    def get_random_id():
        return random.randint(1, 2147483647)

    @staticmethod
    def _clean_all_tag_from_str(string_line):
        """
        Очистка строки stringLine от тэгов и их содержимых
        :param string_line: Очищаемая строка
        :return: очищенная строка
        """
        result = ""
        not_skip = True
        for i in list(string_line):
            if not_skip:
                if i == "<":
                    not_skip = False
                else:
                    result += i
            else:
                if i == ">":
                    not_skip = True

        return result

    @staticmethod
    def price_to_float(price):
        return float(price[:-5].replace(',', '.'))

import vk_api
import random
import requests
import bs4
from transliterate import translit
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bs4 import BeautifulSoup
from favorite_item import add_favorite_item, get_favorite_items


class CsBot:
    def __init__(self, token):
        self.token = token
        self.vk_session = vk_api.VkApi(token=self.token)
        self.long_poll = VkLongPoll(self.vk_session)

        # self.keyboard = VkKeyboard(one_time=True)
        # self.keyboard.add_button('Привет', color=VkKeyboardColor.NEGATIVE)
        # self.keyboard.add_button('Клавиатура', color=VkKeyboardColor.POSITIVE)
        # self.keyboard.add_line()
        # self.keyboard.add_location_button()

        self.meetings = ["привет", "хай", "шалом", "вечер в хату", "hello"]

    def start(self):
        print("Bot is started")
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW:

                if event.to_me:
                    request = event.text
                    user_id = event.user_id
                    print("I get a message:", request)

                    if request.lower() in self.meetings:
                        self._write_msg(user_id, "Шалом")
                    # elif request == "кто я":
                    #     self._write_msg(user_id, self._get_user_by_id(user_id))
                    elif request.lower() == "!избранное":
                        self._send_favorites(user_id)
                    elif "steamcommunity.com/market/listings/" in request:
                        self._add_favorites(user_id, request)
                    else:
                        self._write_msg(user_id, "Ты можешь:\n"
                                                 "добавить предмет в избранное прислав на него ссылку\n"
                                                 "получить информацию о избранных предметах - !Избранное")

    def _write_msg(self, user_id, message):
        print(message, "to", user_id, "was sent")
        self.vk_session.method('messages.send',
                               {'user_id': user_id, 'message': message, "random_id": self.get_random_id()})

    def _add_favorites(self, user_id, url):
        if add_favorite_item(user_id, url) == -1:
            message = "Этот предмет уже в избранном"
        else:
            message = "Предмет добавлен!\nТеперь ты будешь получать информацию о нем!"

        self._write_msg(user_id, message)

    def _send_favorites(self, user_id):
        items = get_favorite_items(user_id)

        if items:
            message = "Твоё избранное:\n"

            for item in items:
                message += ' ' + item["name"] + ':\n' + item["price_fee"] + '\n\n'
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

    def _get_result(self, team):
        url = "https://www.sports.ru/krasnodar/calendar/"

        team_en = translit(team, language_code='ru', reversed=True)
        team_en = team_en.replace("ju", "u").replace("ts", "c").replace("'", "")
        print(team_en)
        url = "https://www.sports.ru/" + team_en + "/calendar/"
        # if team == "краснодар":
        #     url = "https://www.sports.ru/krasnodar/calendar/"
        # elif team == "локомотив":
        #     url = "https://www.sports.ru/lokomotiv/calendar/"
        # elif team == "цска":
        #     url = "https://www.sports.ru/cska/calendar/"
        # elif team == "спартак":
        #     url = "https://www.sports.ru/spartak/calendar/"

        page = requests.get(url)
        print(page.status_code)
        if page.status_code != 200:
            return "Я не смог ничего найти"
        # all_matches = []

        soup = BeautifulSoup(page.text, "html.parser")
        # print(soup)

        soup = soup.find('table', class_="stat-table")
        soup = soup.find('tbody')
        all_matches = soup.findAll('tr')

        final_stats = []
        for match in all_matches:
            match_stats = match.findAll('a')
            filtered_stats = []
            for stat in match_stats:
                # stat = re.sub('\\n$', '', stat.text)
                filtered_stats.append(self.format_text(stat.text))
            stats = {"date": filtered_stats[0], "competition": filtered_stats[1], "opponent": filtered_stats[2],
                     "score": filtered_stats[3]}
            final_stats.append(stats)

        return final_stats[0]["date"] + '\n' + team.capitalize() + ' ' + final_stats[0]["score"] + ' ' + final_stats[0][
            "opponent"]

    def _send_result(self, user_id, message):
        # team = message.replace("последний матч", "")
        # team = team.replace(" ", "")
        # text = self._get_result(team)
        # self._write_msg(user_id, text)
        pass

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

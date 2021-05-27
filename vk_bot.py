import vk_api
import random
import requests
import bs4
from transliterate import translit
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bs4 import BeautifulSoup


class VkBot:
    def __init__(self, token):
        self.token = token
        self.vk_session = vk_api.VkApi(token=self.token)
        self.long_poll = VkLongPoll(self.vk_session)

        self.keyboard = VkKeyboard(one_time=True)
        self.keyboard.add_button('Привет', color=VkKeyboardColor.NEGATIVE)
        self.keyboard.add_button('Клавиатура', color=VkKeyboardColor.POSITIVE)
        self.keyboard.add_line()
        self.keyboard.add_location_button()

        self.meetings = ["привет", "хай", "шалом", "вечер в хату", "hello"]

    def start(self):
        print("Bot is started")
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW:

                if event.to_me:
                    request = event.text.lower()
                    print("I get a message:", request)

                    if request in self.meetings:
                        self._write_msg(event.user_id, "Шалом")
                    elif request == "кто я":
                        self._write_msg(event.user_id, self._get_user_by_id(event.user_id))
                    elif request == "команды":
                        if event.from_user:
                            self._send_keyboard(event.user_id)
                    elif "последний матч" in request:
                        self._send_result(event.user_id, request)
                    else:
                        self._write_msg(event.user_id, "Ты несешь херню")

    @staticmethod
    def format_text(str):
        result = ""
        for i in range(0, len(str)):
            if str[i] != '\n':
                result += str[i]
        return result

    def _get_result(self, team):
        url = "https://www.sports.ru/krasnodar/calendar/"

        url = "https://www.sports.ru/" + translit(team, language_code='ru', reversed=True) + "/calendar/"
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
        # team = "краснодар"
        # if "краснодар" in message:
        #     team = "краснодар"
        # elif "локомотив" in message:
        #     team = "локомотив"
        # elif "цска" in message:
        #     team = "цска"
        # elif "спартак" in message:
        #     team = "спартак"
        team = message.replace("последний матч", "")
        team = team.replace(" ", "")
        text = self._get_result(team)
        self._write_msg(user_id, text)

    def _write_msg(self, user_id, message):
        print(message, "to", user_id, "was sent")
        self.vk_session.method('messages.send',
                               {'user_id': user_id, 'message': message, "random_id": self.get_random_id()})

    def _send_keyboard(self, user_id):
        print("keyboard to", user_id, "was sent")
        self.vk_session.method('messages.send',
                               {"user_id": user_id,
                                "random_id": self.get_random_id(),
                                "keyboard": self.keyboard.get_keyboard(),
                                "message": 'Держи'})
        # self.vk_session.messages.send(
        #     user_id=user_id,
        #     random_id=self.get_random_id(),
        #     keyboard=self.keyboard.get_keyboard(),
        #     message='Держи'
        # )

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

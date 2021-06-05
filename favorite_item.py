import random
import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'ru-UA,ru;q=0.9,en-US;q=0.8,en;q=0.7,ru-RU;q=0.6',
}


def forgot_favorite(user_id, id):
    # items = get_favorite_items(user_id)
    line = find_line(user_id)
    # print(line)
    cut_line(line)
    new_line = str(user_id) + ' :'
    # print(new_line)
    items = line.split(' : ')[1].split(' ')
    # print(items)
    # print(len(items))

    if id < 0 < len(items) < id:
        return -1
    for item in items:
        print(item)
        id -= 1
        if id != 0:
            new_line += ' ' + item
    # print(new_line)
    write_line(new_line)
    return 0


def cut_name(tag_context):
    if tag_context:
        return str(tag_context).split('>')[1].split('<')[0]
    return None


def add_favorite_item(user_id, item):
    if "steamcommunity.com/market/listings/" in item:
        item = item_from_url(item)
    user_id = str(user_id)
    # print(user_id)
    line = find_line(user_id)

    # print(line)
    # print(item)
    if not line:
        line = user_id + ' : ' + item

        file_in = open('fav_csgo.txt', 'a')
        file_in.write(line + '\n')
        file_in.close()

    else:
        read_items_str = line[line.find(':') + 2:]
        read_items = read_items_str.split(' ')

        if item in read_items:
            # print("Team is already added")
            return -1
        else:
            # print(item)
            cut_line(line)
            line += ' ' + item

            file_in = open('fav_csgo.txt', 'a')
            file_in.write(line + '\n')
            file_in.close()
    return 0


def get_item_name(item):
    steam_link = ('https://steamcommunity.com/market/listings/730/' + item)
    print(steam_link)

    full_page = requests.get(steam_link, headers=headers)
    soup = BeautifulSoup(full_page.content, 'html.parser')

    name_tag = soup.find_all('div', class_="market_listing_nav")
    try:
        return str(name_tag).split('</a>')[1].split(">")[1]
    except Exception:
        print("Error with access to steam market")
        return "Ошибка"


def get_favorite_names(user_id, items_base):
    items = get_items_from_line(find_line(user_id))

    item_names = []
    for item in items:
        name = items_base[item][0]

        steam_link = "https://steamcommunity.com/market/priceoverview/?currency=5&appid=730&market_hash_name=" + item

        prise_fee = None
        while not prise_fee:
            prise_fee = requests.get(steam_link).json()

        prise_fee = prise_fee["lowest_price"]

        item = {"name": name, "item_id": item, "price_fee": prise_fee, "price_no_fee": prise_fee}
        item_names.append(item)

    # print(item_names)
    return item_names


def get_items_from_line(line):
    if line:
        return line[line.find(':') + 2:].split(' ')
    else:
        return []


def cut_line(line):
    file_out = open('fav_csgo.txt', 'r')
    lines = file_out.readlines()
    lines.remove(line + '\n')
    file_out.close()

    find_in = open('fav_csgo.txt', 'w')
    find_in.writelines(lines)
    find_in.close()


def write_line(line):
    file_in = open('fav_csgo.txt', 'a')
    file_in.write(line + '\n')
    file_in.close()


def find_line(user_id):
    user_id = str(user_id)

    file_out = open('fav_csgo.txt', 'r')
    for line in file_out:
        if line.find(user_id) != -1:
            file_out.close()
            return line[:-1]

    file_out.close()
    return None


def item_from_url(url):
    return url.split('730/')[1].replace('/', '')


def get_all_users():
    users = []

    file_out = open('fav_csgo.txt', 'r')
    for line in file_out:
        users.append(line.split(" : ")[0])

    file_out.close()
    return users


def get_all_favorite_items():
    all_items = []

    for user_id in get_all_users():
        items = get_items_from_line(find_line(user_id))

        for item in items:
            if item not in all_items:
                all_items.append(item)

    return all_items


def get_items_info(items):
    item_dict = {}

    for item in items:
        steam_link = "https://steamcommunity.com/market/priceoverview/?currency=5&appid=730&market_hash_name=" + item

        prise_fee = None
        while not prise_fee:
            prise_fee = requests.get(steam_link).json()

        prise_fee = prise_fee["lowest_price"]

        item_dict[item] = [get_item_name(item), prise_fee]
    return item_dict

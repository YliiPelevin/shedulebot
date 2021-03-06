import requests
import telebot
import config
import time
import datetime
from bs4 import BeautifulSoup
from typing import Optional

bot = telebot.TeleBot(config.token)
week_list = ['/monday', '/tuesday', '/wednesday', '/thursday', '/friday', '/saturday']
visual_list = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу']


def get_page(group='K3140', week='') -> str:
    if week:
        week = str(week) + '/'
    if week == '0/':
        week = ''
    url = '{domain}/0/{group}/{week}raspisanie_zanyatiy_{group}.htm'.format(
        domain=config.domain,
        week=week,
        group=group)
    response = requests.get(url)
    web_page = response.text
    return web_page


def get_schedule(web_page, day):
    soup = BeautifulSoup(web_page, "html5lib")

    # Получаем таблицу с расписанием на день недели
    if day in week_list:
        number = str(week_list.index(day) + 1) + 'day'
    else:
        number = '1day'
    schedule_table = soup.find('table', attrs={'id': number})
    if not schedule_table:
        return

    # Время проведения занятий
    times_list = schedule_table.find_all("td", attrs={"class": "time"})
    times_list = [time.span.text for time in times_list]

    # Место проведения занятий
    locations_list = schedule_table.find_all("td", attrs={"class": "room"})
    locations_list = [room.span.text for room in locations_list]

    # Название дисциплин и имена преподавателей
    lessons_list = schedule_table.find_all("td", attrs={"class": "lesson"})
    lessons_list = [lesson.text.replace('\n', '').replace('\t', '') for lesson in lessons_list]

    return times_list, locations_list, lessons_list


@bot.message_handler(commands=['all'])
def get_week(message):
    try:
        _, week, group = message.text.split()
    except:
        bot.send_message(message.chat.id, 'Данные введены неверно или не полностью.')
        return None
    web_page = get_page(group, week)

    if int(week) == 1:
        resp = '<b>Расписание группы ' + str(group) + ' на четную неделю:</b>\n\n'
    elif int(week) == 2:
        resp = '<b>Расписание группы ' + str(group) + ' на нечетную неделю:</b>\n\n'
    else:
        resp = '<b>Все расписание группы ' + str(group) + ':</b>\n\n'

    for day in week_list:
        resp += '<b>' + visual_list[week_list.index(day)] + '</b>' + ':\n'
        schedule = get_schedule(web_page, day)
        if not schedule:
            continue

        times_lst, locations_lst, lessons_lst = schedule
        for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):
            resp += '<b>{}</b>, {}, {}\n'.format(time, location, lesson)
        resp += '\n'
    bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['tomorrow'])
def get_tomorrow(message):
    try:
        _, group = message.text.split()
    except:
        bot.send_message(message.chat.id, 'Данные введены неверно или не полностью.')
        return None
    _, group = message.text.split()
    today = datetime.datetime.now().weekday()


    if today== 5:
        bot.send_message(message.chat.id, 'Завтра воскресенье, отдохни')
        return

    if int(datetime.datetime.today().strftime('%U')) % 2 == 1:
        week = 1
    else:
        week = 2
    web_page = get_page(group, str(week))
    today = datetime.datetime.now() + datetime.timedelta(days=1)
    tomorrow = today
    if today.weekday() == 7:
        tomorrow = today + datetime.timedelta(days=1)
    tomorrow = week_list[tomorrow.weekday()]
    schedule = get_schedule(web_page, tomorrow)
    if not schedule:
        bot.send_message(message.chat.id, 'Завтра у указанной группы нет занятий')
        return None

    times_lst, locations_lst, lessons_lst = schedule
    resp = '<b>Расписание на завтра:\n\n</b>'
    for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):
        resp += '<b>{}</b>, {}, {}\n'.format(time, location, lesson)

    bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'])
def get_day(message):
    try:
        day, week, group = message.text.split()
    except:
        bot.send_message(message.chat.id, 'Данные введены неверно или не полностью.')
        return None
    web_page = get_page(group, week)
    schedule = get_schedule(web_page, day)
    if not schedule:
        bot.send_message(message.chat.id, 'В указанный день у группы нет занятий')
        return None

    times_lst, locations_lst, lessons_lst = schedule

    resp = ''
    for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):
        resp += '<b>{}</b>, {}, {}\n'.format(time, location, lesson)

    bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['near'])
def get_next_lesson(message):
    try:
        _, group = message.text.split()
    except:
        bot.send_message(message.chat.id, 'Данные введены неверно или не полностью.')
        return None
    today = datetime.datetime.now().weekday()
    if today != 6:
        today = week_list[today]
    else:
        bot.send_message(message.chat.id, 'Сегодня воскресенье, отдохни')

    while True:
        count = 0
        if int(datetime.datetime.today().strftime('%U')) % 2 == 1:
            week = '1'
        else:
            week = '2'
        web_page = get_page(group, week)
        schedule = get_schedule(web_page, today)
        if not schedule:
            if today != '/saturday':
                today = week_list[week_list.index(today) + 1]
            else:
                today = '/monday'
            count += 1
        else:
            break

    times_lst, locations_lst, lessons_lst = schedule
    cnt = 0
    state = 0
    for i in times_lst:
        try:
            _, time = i.split('-')
        except:
            bot.send_message(message.chat.id, 'ЦК')
            return
        t1, t2 = time.split(':')
        time = int(t1 + t2)
        cur_time = int(str(datetime.datetime.now().hour) + str(datetime.datetime.now().minute))
        if cur_time < time:
            resp = '<b>Твоя ближайшая пара в ' + visual_list[week_list.index(today)] + ':</b>\n'
            resp += '<b>{}</b>, {}, {}\n'.format(times_lst[cnt], locations_lst[cnt], lessons_lst[cnt])
            bot.send_message(message.chat.id, resp, parse_mode='HTML')
            state = 1
            break
        cnt += 1
    if not state:
        while True:

            today = datetime.datetime.now() + datetime.timedelta(days=count)
            tomorrow = today
            if today.weekday() == 5:
                tomorrow += datetime.timedelta(days=2)
            else:
                tomorrow += datetime.timedelta(days=1)

            tomorrow = week_list[tomorrow.weekday()]

            schedule = get_schedule(web_page, tomorrow)
            if not schedule:
                count += 1
                continue

            times_lst, locations_lst, lessons_lst = schedule
            resp = '<b>{}</b>, {}, {}\n'.format(times_lst[0], locations_lst[0], lessons_lst[0])
            bot.send_message(message.chat.id, resp, parse_mode='HTML')
            break


while True:
    try:
        bot.polling(none_stop=True)
    except:
        time.sleep(5)

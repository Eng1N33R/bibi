import re
import time
import json
import random
import datetime
import sys
import traceback

from config import config
import sheets
import vk_api

class State:
    def __init__(self):
        try:
            with open('data.json') as fh:
                self.state = json.load(fh)
        except FileNotFoundError:
            self.state = {}
    
    def get(self, address, throw=False, default=None):
        """Recursive deep get for the state object.

        `address` is specified as a slash-delimited (/) string.

        If `throw` is `True`, throws an exception if any part of the address
        doesn't exist. Otherwise, returns `default` and sets the address to
        that value using {#set}.
        """
        comps = address.split('/')
        try:
            cursor = self.state[comps[0]]
        except Exception as e:
            if throw:
                raise e
            else:
                self.set(address, default)
                return default
        i = 1
        while i < len(comps)-2:
            try:
                cursor = cursor[comps[i]]
            except Exception as e:
                if throw:
                    raise e
                else:
                    self.set(address, default)
                    return default
            i += 1
        try:
            return cursor[comps[len(comps)-1]]
        except Exception as e:
            if throw:
                raise e
            else:
                self.set(address, default)
                return default

    def set(self, address, value):
        """Recursive deep set for the state object.

        `address` is specified as a slash-delimited (/) string.
        """
        comps = address.split('/')
        try:
            cursor = self.state[comps[0]]
        except:
            cursor = {}
            self.state[comps[0]] = cursor
        i = 1
        while i < len(comps)-2:
            try:
                cursor = cursor[comps[i]]
            except:
                cursor[comps[i]] = {}
                cursor = cursor[comps[i]]
            i += 1
        try:
            cursor[comps[len(comps)-1]] = value
        except:
            cursor = {comps[len(comps)-1]: value}
            cursor[comps[len(comps)-1]] = cursor
    
    def save(self):
        with open('data.json', 'w') as fh:
            json.dump(self.state, fh)

class Context:
    def __init__(self, user_id):
        self.user_id = user_id
        try:
            self.context = memory['context'][user_id]
        except:
            self.context = {}
            memory['context'][user_id] = self.context
    
    def get(self, address):
        return memory['context'][self.user_id][address]
    
    def set(self, address, value):
        memory['context'][self.user_id][address] = value

state = State()
memory = {'seconds_counter': 0, 'context': {}}

vk = vk_api.VkApi(token=config['VK_TOKEN'])
sheets.acquire_auth()
# All other acquire_auth calls are commented for now to see how Google behaves

tasks = {}
def task(txt):
    return lambda f: tasks.setdefault(txt, f)

final_name_pattern = re.compile(r'(\w+).?$')

@task((r'.*?список группы', r'.*?состав группы'))
def process_student_list(user_id, txt):
    #sheets.acquire_auth()
    values = sheets.get_range_values('Список группы!A3:B')
    name_list = []
    for row in values:
        name_list.append('%s. %s' % (row[0], row[1]))
    say(user_id, '👫 Список группы:\n\n' + '\n'.join(name_list))

@task((r'какой у меня вариант', r'.*?мой вариант'))
def process_student_selfnumber(user_id, txt):
    global state
    try:
        name = state.get('names/%d' % user_id, throw=True)
    except:
        response = vk.method('users.get', {'user_ids': user_id, 'fields': 'last_name'})
        name = response[0]['last_name']
    #sheets.acquire_auth()
    values = sheets.get_range_values('Список группы!A3:G')
    for row in values:
        if row[6] == name:
            say(user_id, '🔢 Твой вариант — №%s!' % (row[0]))
            return
    say(user_id, '❗ В группе не числится студент с фамилией %s! Может, ты сидишь под псевдонимом? '
        'В таком случае напиши «моя фамилия Х», и я запомню твой псевдоним.' % (name))

@task((r'какой вариант у', r'вариант'))
def process_student_othernumber(user_id, txt):
    global state
    name = final_name_pattern.search(txt).group(1)
    if name == 'меня':
        return process_student_selfnumber(user_id, txt)

    name = name[:1].upper() + name[1:]
    #sheets.acquire_auth()
    values = sheets.get_range_values('Список группы!A3:G')
    for row in values:
        if row[6][:len(row[6])-4] in name:
            say(user_id, '🔢 %s: вариант №%s' % (row[6], row[0]))
            return
    say(user_id, '❗ В группе не числится студент с фамилией %s! Ты точно правильно её указал?' % (name))

@task((r'моя фамилия', r'меня зовут'))
def process_student_alias(user_id, txt):
    global state
    name = final_name_pattern.search(txt).group(1)
    name = name[:1].upper() + name[1:]
    print('recording alias %s for user ID %d' % (name, user_id))
    state.set('names/%d' % (user_id), name)
    say(user_id, '👤 Запомнила твой псевдоним!')

@task((r'какое отчество у', r'как зовут'))
def process_student_patronymic(user_id, txt):
    global state
    #sheets.acquire_auth()
    name = final_name_pattern.search(txt).group(1)
    name = name[:1].upper() + name[1:]
    values = sheets.get_range_values('Список группы!A3:G')
    for row in values:
        if row[6][:len(row[6])-4] in name:
            full_name = row[1]
            say(user_id, '✒ %s' % (full_name))
            return
    say(user_id, '❗ В группе не числится студент с фамилией %s! Ты точно правильно её указал?' % (name))

@task((r'что ты можешь', r'как( \w+)? пользоваться', r'.*?помощь', r'.*?х(е|э)лп', r'.*?help'))
def process_help(user_id, txt):
    say(user_id, '❓ Я поддерживаю такие команды:\n\n'
        '➡ "с какой завтра" — показать порядковый номер самой ранней пары завтра\n'
        '➡ "какие завтра пары" — показать расписание на завтра\n'
        '➡ "какой у меня вариант" — показать твой вариант (номер по списку)\n'
        '➡ "список группы" — показать список всей группы\n'
        '➡ "какой вариант у <фамилия>" — показать вариант (номер по списку) другого студента\n'
        '➡ "как зовут <фамилия>" — показать полное имя студента\n'
        '➡ "кто ты" — показать информацию о системе\n'
        '\n'
        'Я не совсем глупая и понимаю эти команды, даже если ты скажешь их немного иначе, но я ещё только учусь!'
        '\n'
        'Если я работаю неисправно, пожалуйста, сообщи об этом моему разработчику, Илье Гаврикову (Илья Виртуальный). '
        'Буду очень признательна!'
    )

@task((r'спасибо', r'спс', r'сяб', r'сенкс', r'пасиб'))
def process_thanks(user_id, txt):
    replies = [
        'Не за что 😊',
        'Пожалуйста 🙂',
        'Обращайся 😉'
    ]
    say(user_id, random.choice(replies))

def get_schedule_for_day(day, denom):
    #sheets.acquire_auth()
    offset = 2 if denom else 0
    values = sheets.get_range_values('Расписание!A4:H28')
    processing = False
    schedule = []
    row_i = 0
    for row in values:
        if processing:
            row_i += 1
        if len(row) == 0:
            continue
        if (row[0].startswith('wd')):
            if (row[0] == 'wd%d' % (day)):
                processing = True
            else:
                if processing:
                    processing = False
                    break
            continue
        if processing:
            if row[1+offset] != '':
                schedule.append((row_i, row[1+offset], row[5], row[6]))
    return schedule

day_pattern = re.compile(r'во? (\w+)', re.U)
def get_day_by_name(txt):
    day_search = day_pattern.search(txt.lower())
    try:
        day = day_search.group(1)
    except:
        return None

    days = ('понедельник', 'вторник', 'среду', 'четверг',
            'пятницу', 'субботу', 'воскресенье')
    if day in days:
        dayindex = days.index(day) + 1
    else:
        return None
    return (dayindex, days[dayindex-1])

def get_denom_now():
    #sheets.acquire_auth()
    return sheets.get_cell_value('Расписание!H2') == 'TRUE'

def get_relative_schedule(day):
    if day == None:
        return (-1)
    if day[0] in (6, 7):
        return (-2)

    today = datetime.datetime.today() - datetime.timedelta(hours=3)
    wd = today.weekday()+1
    denom_now = get_denom_now()
    denom_tgt = not denom_now if wd > day[0] and wd not in (
        6, 7) else denom_now

    return get_schedule_for_day(day[0], denom_tgt)

def get_class_index(time):
    schedule = sheets.get_range_values('Расписание!E39:G44')
    for row in schedule:
        if time == row[1]:
            return int(row[0])
    return None

@task((r'какие завтра пары', r'пары завтра', r'.*?что за пары завтра'))
def process_schedule_tomorrow(user_id, txt):
    today = datetime.datetime.today() - datetime.timedelta(hours=3)
    wd = today.weekday()+1
    if wd in (5, 6):
        say(user_id, '🕑 Завтра выходной! 😃')
        return
    tomorrow = 1 if wd == 7 else wd+1
    schedule = get_schedule_for_day(tomorrow, get_denom_now())
    class_list = [ '%s—%s | %s' % (day[2], day[3], day[1]) for day in schedule ]
    say(user_id, '📅 Завтра будут такие пары:\n\n%s' % ('\n'.join(class_list)))

@task((r'(с|к) какой завтра', r'(со|к) скольки завтра'))
def process_arrival_tomorrow(user_id, txt):
    today = datetime.datetime.today() - datetime.timedelta(hours=3)
    wd = today.weekday()+1
    if wd in (5, 6):
        say(user_id, '🕑 Завтра выходной! 😃')
        return
    tomorrow = 1 if wd == 7 else wd+1
    schedule = get_schedule_for_day(tomorrow, get_denom_now())
    class_index = get_class_index(schedule[0][2])
    if class_index == 0:
        say(user_id, '🕑 Завтра нет пар!')
    words = ('к первой', 'ко второй', 'к третьей',
             'к четвёртой', 'к пятой', 'к шестой')
    say(user_id, '🕑 Завтра %s (%s)!' % (words[class_index-1], schedule[0][2]))

@task((r'сколько завтра пар', r'сколько пар завтра'))
def process_classes_tomorrow(user_id, txt):
    #sheets.acquire_auth()
    today = datetime.datetime.today() - datetime.timedelta(hours=3)
    wd = today.weekday()+1
    if wd in (5, 6):
        say(user_id, '🕑 Завтра выходной! 😃')
        return
    tomorrow = 1 if wd == 7 else wd+1

    schedule = get_schedule_for_day(tomorrow, get_denom_now())
    n = len(schedule)
    words = ('нет пар', 'одна пара', 'две пары', 'три пары',
             'четыре пары', 'пять пар', 'шесть пар')
    say(user_id, '🕑 Завтра %s!' % (words[n]))

@task((r'.*?какие пары во? (\w+)', r'пары во? (\w+)', r'.*?что за пары во? (\w+)'))
def process_schedule_day(user_id, txt):
    day = get_day_by_name(txt)
    schedule = get_relative_schedule(day)
    if schedule[0] == -1:
        return say(user_id, '🤷‍♀️ Не поняла, о каком ты спрашиваешь дне. Уточни, пожалуйста.')
    if schedule[0] == -2:
        return say(user_id, '🕑 Это неучебный день!')

    class_list = ['%s—%s | %s' % (day[2], day[3], day[1]) for day in schedule]
    say(user_id, '📅 В%s %s будут такие пары:\n\n%s' %
        ('о' if day[0] == 2 else '', day[1], '\n'.join(class_list)))

@task((r'(с|к) какой во? (\w+)', r'(со|к) скольки во? (\w+)'))
def process_arrival_day(user_id, txt):
    day = get_day_by_name(txt)
    schedule = get_relative_schedule(day)
    if schedule[0] == -1:
        return say(user_id, '🤷‍♀️ Не поняла, о каком ты спрашиваешь дне. Уточни, пожалуйста.')
    if schedule[0] == -2:
        return say(user_id, '🕑 Это неучебный день!')

    class_index = get_class_index(schedule[0][2])
    words = ('к первой', 'ко второй', 'к третьей',
             'к четвёртой', 'к пятой', 'к шестой')
    say(user_id, '🕑 В%s %s %s (%s)!' %
        ('о' if day[0] == 2 else '', day[1], words[class_index-1], schedule[0][2]))

@task((r'сколько пар во? (\w+)'))
def process_classes_day(user_id, txt):
    #sheets.acquire_auth()
    day = get_day_by_name(txt)
    schedule = get_relative_schedule(day)
    if schedule[0] == -1:
        return say(user_id, '🤷‍♀️ Не поняла, о каком ты спрашиваешь дне. Уточни, пожалуйста.')
    if schedule[0] == -2:
        return say(user_id, '🕑 Это неучебный день!')

    n = len(schedule)
    words = ('нет пар', 'одна пара', 'две пары', 'три пары',
             'четыре пары', 'пять пар', 'шесть пар')
    say(user_id, '🕑 В%s %s %s!' %
        ('о' if day[0] == 2 else '', day[1], words[n]))

@task((r'кто ты', r'ты кто'))
def process_easteregg_introduction(user_id, txt):
    say(user_id,
        '🙋‍♀️ Привет! Меня зовут Биби (ударение на последний слог). Моё имя никак не расшифровывается, но оно созвучно с БИ — сокращением от '
        '«бизнес-информатика». Совпадение? Не знаю, не мне судить. Быть может, оно означает «тётя» на персидском, или «я пила» на латыни — кто знает?\n\n'

        '🎓 Я автоматизированная система поддержки учебного процесса. Много длинных слов, согласна, но по сути я помогаю студентам не потеряться в таком '
        'запутанном процессе обучения в нашем вузе. Я помогу тебе сориентироваться в учебном расписании и организовать свою работу.\n\n'

        '🛠 Я изо всех сил стараюсь работать правильно, но иногда может быть такое, что я ошибусь и неправильно что-нибудь скажу. Не злись на меня — я '
        'ещё учусь и не всегда могу сама корректировать информацию. В таком случае лучше сообщи об ошибке моему разработчику (Илья Виртуальный) — он её '
        'обязательно исправит.\n\n'

        '💬 Не стесняйся задавать мне вопросы — я понимаю разные формулировки, если, конечно, ты пишешь более-менее грамотно 😉 Чтобы получить полный и '
        'актуальный список запросов, скажи мне «что ты можешь», и я отвечу. Надеюсь, я буду тебе полезна! 😊')

@task((r'привет', r'хай', r'ку(\)|!|.|\(|\?)+$', r'даров', r'здоров', r'дратути'))
def process_easteregg_hi(user_id, txt):
    say(user_id, 'И тебе привет 🙂')

@task((r'пока', r'бай', r'бб', r'досвидос', r'до свидания'))
def process_easteregg_bye(user_id, txt):
    say(user_id, 'До скорой встречи 😉')

@task((r'извини', r'сор+(и|ь|ян)'))
def process_easteregg_sorry(user_id, txt):
    say(user_id, 'Ничего страшненького 👨🏿')

@task((r'молодец'))
def process_easteregg_goodjob(user_id, txt):
    say(user_id, 'Спасибо! ♥')

@task((r'си+', r'si+', r'sì+'))
def process_meme_si(user_id, txt):
    replies = [
        'Il signore è italiano? Che sorpresa!',
        'Ah, il classico!',
        'Lasciatemi cantare... 🎶',
        'Assolutamente corretto.'
    ]
    say(user_id, '🇮🇹 %s' % (random.choice(replies)))

@task((r'я+ зде+сь', r'.*?д(о|а)лб(о|а)(е|ё)б', r'да( |-)?да ?я'))
def process_meme_yazdes(user_id, txt):
    replies = [
        'Да, да, я, да.',
        'Ну шо вы деда дразните?',
        'Всем привет, я Биби, мне тринадцать лет и я пользуюсь программой для изменения голоса.',
        'Да это всё брат мой, дебил.'
    ]
    say(user_id, '🧓 %s' % (random.choice(replies)))

@task((r'.*?глютен'))
def process_meme_gluten(user_id, txt):
    replies = [
        'Согласно Указу Президента Москольцовской республики Даниила Ширина, все глютеносодержащие продукты облагаются обязательным налогом в 13,5%.',
        'Да ладно, всего кусочек хлеба, чего тебе от него будет?',
        'Это тебе, получается, нельзя хлеб? А чёрный? А тосты? А сухарики? А мясо в кляре? А в панировке?..',
        'Глютеновое небо, глютеновое море, глютеновая зелень, глютеновый верблюд. Глютеновые мамы глютеновым ребятам глютеновые песни глютеново поют.'
    ]
    say(user_id, '🍞 %s' % (random.choice(replies)))

@task((r'а+м', r'при+п', r'пи+п', r'ши+ш'))
def process_meme_pitash(user_id, txt):
    replies = [
        'Ам прип.',
        'Пиип шииш.',
        '🤛 Ну привет!',
        'Привет, тонкий!'
    ]
    say(user_id, '👋 %s' % (random.choice(replies)))

@task((r'эбсолютли райт', r'класс?ик', r'йес'))
def process_meme_soldatov(user_id, txt):
    replies = [
        'Эбсалютли райт.',
        'Оо, вы из Англии?'
    ]
    say(user_id, '🇬🇧 %s' % (random.choice(replies)))

@task((r'.*?(кур|дым)(ишь|им|ить|ил|ила)'))
def process_meme_smoking(user_id, txt):
    replies = [
        'Мне, пожалуйста, Аль-Факер, чтоб покрепче. Чего-нибудь свеженького.',
        'У нас сейчас генеральная уборка, через полчаса где-то приходите.',
        'Там Миша пока спит, погодите часика пол.',
        'В Нарджу? Или в Картель?',
        'Подразвезло.'
    ]
    say(user_id, '🌫 %s' % (random.choice(replies)))

@task((r'ну'))
def process_meme_nu(user_id, txt):
    say(user_id, '', extra={'attachment': 'audio33517630_456239323'})

@task((r'машал+а', r'иншал+а', r'аль(х|h)амдулил+а', r'бисмил+а'))
def process_meme_islam(user_id, txt):
    say(user_id, '!بِسْمِ اللهِ الرَّحْمنِ الرَّحِيمِ ☪')

@task((r'.*?антихайп', r'бр+я'))
def process_meme_antihype(user_id, txt):
    replies = [
        'Бррррррррррря!',
        'Антихайп.',
        'Раунд!',
    ]
    say(user_id, '🎵 %s' % (random.choice(replies)))

def process_unknown(user_id, txt):
    say(user_id, '🤷‍♀️ Извини, но я не знаю, что значит «%s». Попробуй сказать иначе, или сообщи о неисправности Илье, моему разработчкику.' % (txt))

def process_stickers(user_id, sticker_id):
    stickers = [4539, 4522, 86, 1]
    say(user_id, '', extra={'sticker_id': random.choice(stickers)})

def process_tasks(user_id, txt):
    for key in tasks:
        if isinstance(key, tuple):
            for pat in key:
                if re.match(pat, txt.lower()):
                    tasks[key](user_id, txt)
                    return
        else:
            if re.match(key, txt.lower()):
                tasks[key](user_id, txt)
                return
    process_unknown(user_id, txt)

def say(user_id, txt, extra={}):
    send = {'user_id': user_id, 'message': txt}
    send.update(extra)
    vk.method('messages.send', send)

def main():
    try:
        while True:
            response = vk.method('messages.get', {'out': 0, 'count': 1})
            for item in response['items']:
                # Check if this message has been processed already
                txt = item[u'body']
                user_id = item[u'user_id']
                last_id = state.get('%d/last_id' % (user_id), default=0)
                if item[u'id'] <= last_id: # Do not process old messages
                    continue
                # Do not process read messages older than 15 seconds
                if item[u'read_state'] == 1 and datetime.datetime.now() - item[u'date'] > 15:
                    continue
                if item[u'out'] == 1: # Do not process outbound messages
                    continue

                if (txt == ''):
                    if item[u'attachments'][0][u'type'] == u'sticker':
                        process_stickers(user_id, item[u'attachments'][0][u'sticker'][u'id'])
                else:
                    process_tasks(item[u'user_id'], txt)

                state.set('%d/last_id' % (user_id), item[u'id'])
            time.sleep(1)
    except KeyboardInterrupt:
        state.save()
    except Exception as e:
        print('Caught exception:')
        ln = sys.exc_info()[-1].tb_lineno
        print('line %d: %s' % (ln, e))
        state.set('%d/last_id' % (user_id), item[u'id'])
        try:
            say(user_id, '🛠 Извини, что-то пошло не так, и я не смогла обработать твой запрос. '
                'Попробуй ещё раз, или подожди немного. Если это происходит слишком часто, сообщи об этом моему '
                'разработчику.'
                '\n\n'
                'Ошибка на строке %d: %s' % (ln, e))
        except:
            pass
        main()

if __name__ == '__main__':
    main()

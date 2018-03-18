# Bibi

Bibi (stress on the last syllable) is a chat bot for VK student communities,
designed to assist students in organising their work. It informs students of
class scheduling, assignment status and details, and other various things
related to university study.

The bot is designed to work in tandem with a Google Sheets document tailored to
a student group. This allows for a simple way to store and represent data
even for non-experts. An example of the Google Sheets document used by the
author's university group is available [at this location](https://docs.google.com/spreadsheets/d/1XThwpYn9mhiAJ-mUf6LOxLCIE5ysCfKbbSNB4a-AQ_4/edit?usp=sharing).

## Implementation details

Bibi's "tasks" are processor functions linked to one or several regular
expressions evaluated against text sent to the community by students. This
allows for simple extensibility of Bibi's existing functions and their
adjustment according to a certain configuration's needs.

## Naming

The stock version of the chat bot is named Bibi and uses a female persona to
communicate with humans. This may be changed depending on your needs. Publicity
materials concerning the bot will, however, refer to it as "she".

## Installation

This bot requires Python 3.5+ to work (tested under 3.6.4).

To install the bot, clone this repository and install its dependencies:

```bash
pip install --upgrade google-api-python-client vk_api
```

Next, create a `config.json` file alongside `config.py`. The JSON file must
contain an object with three values:
- `SPREADSHEET`, containing the Google Sheets spreadsheet ID
- `VK_TOKEN`, containing the VK community access token generated on its settings
page
- `APPLICATION_NAME`, the user agent for interfacing with the Google API
(specified in the console when creating the OAuth key)

Also create alongside the config file a `client_secret.json` file, which
contains the client secret and other properties of your Google API access. This
file may be generated from the Google API Console; detailed instructions about
this process are available [at this location](https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the_api_name).
**Both of these files must be kept secret!**

Now simply run `python chatbot.py`.

# Биби

Биби (ударение на последний слог) — чат-бот для студенческих сообществ
Вконтакте, разработанный для помощи студентам в организации их работы. Он
информирует студентов о расписании пар, статусе и деталях заданий и других
аспектов учебного процесса в вузе.

Он ориентирован на тесное взаимодействие с документом Google Sheets,
разработанным под конкретную студенческую группу. Это позволяет представлять и
хранить данные доступным образом даже для неэкспертов. Пример документа
Google Sheets, используемого университетской группой автора, доступен
[по этой ссылке](https://docs.google.com/spreadsheets/d/1XThwpYn9mhiAJ-mUf6LOxLCIE5ysCfKbbSNB4a-AQ_4/edit?usp=sharing).

## Детали реализации

"Задачи" Биби являются функциями-обработчиками, связанными с одним или
несколькими регулярными выражениями, с которыми сравнивается текст, отправленный
в беседу сообщества студентами. Это делает возможным простое расширение
стандартных функций Биби и их настройка под требования определённой
конфигурации.

## Название

Версия бота, распространяемая из первоисточника, зовётся Биби и использует
женский образ для общения с людьми. Это можно изменить в зависимости от ваших
нужд. Тем не менее, все рекламные материалы, описывающие данный бот, будут
обращаться к нему, используя местоимения женского рода.

## Инсталляция

Данный бот требует для работы Python версии 3.5 или выше (проверено на 3.6.4).

Для установки клонируйте данный репозиторий и установите необходимые библиотеки:

```bash
pip install --upgrade google-api-python-client vk_api
```

Далее, создайте файл `config.json` в папке с `config.py`. Файл JSON должен
содержать объект с тремя значениями:
- `SPREADSHEET`, содержащее ID книги Google Sheets
- `VK_TOKEN`, содержащее ключ доступа сообщества Вконтакте ([инструкции](https://vk.com/dev/access_token?f=2.%20%D0%9A%D0%BB%D1%8E%D1%87%20%D0%B4%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%B0%20%D1%81%D0%BE%D0%BE%D0%B1%D1%89%D0%B5%D1%81%D1%82%D0%B2%D0%B0))
- `APPLICATION_NAME`, юзер-агент для работы с Google API (из консоли Google
при создании OAuth-ключа)

Также в папке необходимо создать файл `client_secret.json`, который содержит
секретный ключ клиента и другие свойства доступа к Google API. Этот файл может
быть сгенерирован автоматически из консоли Google API; детальные инструкции по
этому процессу доступны [по этой ссылке](https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the_api_name).
**Оба файла должны храниться в тайне!**

Теперь просто запустите `python chatbot.py`.
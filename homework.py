import os
import time
import telegram
import requests
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')  # из яндекса
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # из БотФазер
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # Из телеги айди аккаунта

RETRY_PERIOD = 600  # Сколько ждать между новыми запросами
ENDPOINT = os.getenv('ENDPOINT')   # Ссылка откуда брать информацию
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    if (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
            and ENDPOINT) is None:
        raise ValueError('Одна или несколько переменных окружения недоступны')


def send_message(bot, message):
    ...


def get_api_answer(timestamp):
    """GET-запрос к эндпоинту url."""
    homework_statuses = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp},
    )
    return homework_statuses.json()



def check_response(response):
    ...


def parse_status(homework):
    ...

    #return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    ...

    # bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())  # отметка времени
    check_tokens()
    get_api_answer(0)


    """     while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ... """


if __name__ == '__main__':
    main()

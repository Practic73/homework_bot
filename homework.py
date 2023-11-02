import logging
import os
import requests
import sys
import telegram
import time

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    environment_variables = {PRACTICUM_TOKEN, TELEGRAM_TOKEN,
                             TELEGRAM_CHAT_ID}
    for variable in environment_variables:
        if variable is None:
            logger.critical('Переменные окружения не обнаружены')
            sys.exit(1)


def send_message(bot, message):
    """Отправка сообщение."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение отправлено успешно.')
    except telegram.error.TelegramError as error:
        logger.error(f'Ошибка при отправке сообщения - {error}')


def get_api_answer(timestamp):
    """GET-запрос к эндпоинту."""
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp},
        )
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError(
            'Ошибка с доступностью эндпоинта'
        )
    except requests.RequestException as e:
        raise requests.RequestException(
            f'Ошибка при запросе к эндпоинту. Параметры:'
            f'url - {ENDPOINT}'
            f'headers - {HEADERS}'
            f'params - {"from_date": {timestamp}}'
            f'Текст ошибки - {e}')
    else:
        if homework_statuses.status_code != requests.codes.ok:
            raise requests.HTTPError('API возвращает код, отличный от 200')
        return homework_statuses.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    try:
        response['homeworks']
        response['current_date']
    except KeyError:
        raise KeyError('Ошибка. Обязательных ключей не обнаружено')
    if type(response) is not dict:
        raise TypeError(
            f'В ответе API структура данных не соответствует ожиданиям.'
            f'Тип данных ответа - {type(response)}'
        )
    if type(response['homeworks']) is not list:
        raise TypeError('В ответе API домашки под ключом `homeworks`'
                        'данные приходят не в виде списка')


def parse_status(homework):
    """Проверка статуса домашней работы."""
    try:
        homework_name = homework['homework_name']
        status = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        raise KeyError('Отсутствует ключ "homework_name"')
    except ValueError:
        raise ValueError('Неожиданный статус')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        old_message = ''
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if len(response['homeworks']) > 0:
                message = parse_status(response['homeworks'][0])
                send_message(bot, message)
            else:
                logger.debug('Изменений нет')
        except telegram.error.TelegramError:
            logger.error('Ошибка при взаимодействии с Телеграмм')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if old_message != message:
                send_message(bot, message)
        finally:
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

import logging
import os
import sys

import requests
import telegram
import time

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

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
    environment_variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    variable_is_available = True
    for variable, value in environment_variables.items():
        if value is None:
            variable_is_available = False
            logger.critical(f'Переменная {variable} отсутствует')
    if not variable_is_available:
        return False
    return True


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
    if homework_statuses.status_code != requests.codes.ok:
        raise requests.HTTPError('API возвращает код, отличный от 200')
    return homework_statuses.json()


def check_keys_in_response(keys_dictionary):
    """Проверяет наличие значений в словаре."""
    not_found_keys_list = []
    for key, value in keys_dictionary.items():
        if value is None:
            not_found_keys_list.append(key)
    return not_found_keys_list


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            f'В ответе API структура данных не соответствует ожиданиям.'
            f'Тип данных ответа - {type(response)}'
        )
    homeworks = response.get('homeworks')
    keys_in_response = {
        'homeworks': homeworks,
        'current_date': response.get('current_date'),
    }
    result_check_keys = check_keys_in_response(keys_in_response)
    if result_check_keys:
        raise KeyError(f'Обязательные ключи '
                       f'не обнаружены: {result_check_keys}')
    if not isinstance(homeworks, list):
        raise TypeError(
            f'В ответе API структура данных не соответствует ожиданиям.'
            f'Тип данных ответа - {type(homeworks)}'
        )


def parse_status(homework):
    """Проверка статуса домашней работы."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    keys_in_homework = {
        'homework_name': homework_name,
        'status': status,
    }
    result_check_keys = check_keys_in_response(keys_in_homework)
    if result_check_keys:
        raise KeyError(f'Обязательные ключи '
                       f'не обнаружены: {result_check_keys}')
    if status not in HOMEWORK_VERDICTS:
        raise KeyError(f'Полученный статус {status} '
                       'не обнаружен в списке допустимых')
    verdict = HOMEWORK_VERDICTS[status]
    return (f'Изменился статус проверки работы "{homework_name}". {verdict}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        old_message = ''
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks_list = response['homeworks']
            if homeworks_list:
                homework, *other = homeworks_list
                message = parse_status(homework)
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
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    main()

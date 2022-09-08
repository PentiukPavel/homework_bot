import logging
import logging.config
import os
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import GeneralException, HomeWorkIsNotChecked

load_dotenv()

ERROR_LOG_FILENAME = '.bot-errors.log'

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s, %(name)s, %(levelname)s, %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '%(message)s',
        },
    },
    'handlers': {
        'file_logger': {
            'formatter': 'default',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': ERROR_LOG_FILENAME,
        },
        'main_logger': {
            'formatter': 'default',
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        'homework': {
            'level': 'ERROR',
            'handlers': [
                'file_logger',
            ]
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': [
            'main_logger',
        ]
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
LAST_SENT_MESSAGE = ''
RETRY_TIME = 6
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger('homework')


def send_message(bot: telegram.Bot, message: str):
    """Отправка сообщения в Telegram чат."""
    global LAST_SENT_MESSAGE
    bot = bot
    text = message
    chat_id = TELEGRAM_CHAT_ID
    if LAST_SENT_MESSAGE != message:
        try:
            bot.send_message(chat_id, text)
            LAST_SENT_MESSAGE = message
        except Exception as error:
            raise GeneralException('Сообщение не отправлено!') from error


def get_api_answer(current_timestamp) -> dict:
    """Получение ответа от API yandex practicum."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
        logging.debug('Ответ от API получен.')
    except Exception as error:
        raise GeneralException('Нет связи с API yandex practicum!') from error
    if response.status_code != 200:
        raise GeneralException(f'Статус ответа API - {response.status_code}')
    logging.debug('Статус ответа от API - 200.')
    return response.json()


def check_response(response: dict) -> dict:
    """Проверка ответа от API yandex practicum."""
    if not isinstance(response, dict):
        raise TypeError
    response['homeworks']
    logging.debug('Получен список домашних работ.')
    if not isinstance(response['homeworks'], list):
        raise TypeError
    if response['homeworks'] == []:
        raise HomeWorkIsNotChecked
    return response['homeworks']


def parse_status(homework: dict) -> str:
    """Проверка статуса домашней работы."""
    logging.debug(homework)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES.get(homework_status)
    else:
        raise KeyError('Неизвестный статус домашней работы!')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка доступности переменных окружения."""
    env_variables = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(env_variables)


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        message = 'Отсутствуют переменные среды!'
        logger.critical(message)
    while check_tokens() is True:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())
        try:
            response = get_api_answer(current_timestamp)
            response_json = check_response(response)
            message = parse_status(response_json[0])
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        except HomeWorkIsNotChecked:
            message = 'Домашняя работа еще не проверена!'
            logging.info(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

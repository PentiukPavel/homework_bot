class TelegramBotExceptions(Exception):
    """Базовый класс исключений для телеграм бота."""

    pass


class GeneralException(TelegramBotExceptions):
    """Кастомное исключение для работы телеграм бота."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

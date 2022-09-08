class TelegramBotExceptions(Exception):
    pass


class GeneralException(TelegramBotExceptions):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class HomeWorkIsNotChecked(TelegramBotExceptions):
    def __init__(self):
        super().__init__('Домашняя работа еще не проверена!')

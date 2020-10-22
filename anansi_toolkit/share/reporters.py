import telegram
from ..settings import TelegramSettings

class TelegramReport:
    def __init__(self) -> None:
        self.chat_ids = TelegramSettings.ids
        self.bot = telegram.Bot(TelegramSettings.token)

    def send(self, message):
        for _id in self.chat_ids:
            self.bot.send_message(chat_id=_id, text=message)
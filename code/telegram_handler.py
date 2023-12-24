import time
import telebot

from telebot import types


BOT_TOKEN = "6654595906:AAEg185xtzk03m2wz9cjH_oimfuI7idGOfg"  # token for @vkusvill_food_bot


class TelegramHandler:

    ANSWER = {}
    
    def __init__(
        self,
        chat_id,
        bot_token=BOT_TOKEN,
        use_telegram=True,
        bot=None,
    ):
        
        self.chat_id = chat_id

        if bot is not None:

            self.__bot = bot
            self.bot_token = bot.token

        else:

            self.bot_token = bot_token
            self.__initialize_bot()

        self.use_telegram = use_telegram

        self.ANSWER[chat_id] = ""
        
    def __initialize_bot(self):

        self.__bot = telebot.TeleBot(token=self.bot_token, threaded=False)
        
    def send_message(self, message, reply_markup):
        
        try:
        
            message = self.__bot.send_message(self.chat_id, message, parse_mode='Markdown', reply_markup=reply_markup)

            return message
            
        except telebot.apihelper.ApiTelegramException as e:
            
            try:
            
                seconds_to_sleep = int(str(e).split()[-1])
                
            except ValueError:
                
                seconds_to_sleep = 60
                
            time.sleep(seconds_to_sleep)
            
            return self.send_message(message, reply_markup)

    def send_file(self, path_to_file):

        self.__bot.send_document(self.chat_id, path_to_file.open('rb'))

    def __answer(self, reply_message):

        self.ANSWER[reply_message.chat.id] = reply_message.text

    def __ask(self, message, button_list):

        self.ANSWER[self.chat_id] = ""

        if button_list is not None:

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

            button_list = [types.KeyboardButton(button) for button in button_list]

            markup.add(*button_list)

        else:
            markup = types.ForceReply(selective=False)

        message_obj = self.send_message(message, reply_markup=markup)

        self.__bot.register_next_step_handler(message_obj, self.__answer)

        while self.ANSWER[self.chat_id] == "":
            pass

        if self.ANSWER[self.chat_id] in ['stop', 'Stop', 's', 'S']:

            self.log_info("Algorithm is stopped!")

            raise KeyboardInterrupt

        return self.ANSWER[self.chat_id]

    def log_info(
        self,
        message,
    ):

        print(message, end='\n\n', flush=True)

        if self.use_telegram:
            self.send_message(message, reply_markup=types.ReplyKeyboardRemove(selective=False))

    def ask_for_input(
        self,
        message,
        button_list
    ):

        if self.use_telegram:

            print("Answer the question on Telegram now!", end='\n\n', flush=True)

            return self.__ask(message, button_list)

        answer = input(message + "\n")
        print(flush=True)

        return answer

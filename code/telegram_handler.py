import time
import telebot

from telebot import types


BOT_TOKEN = "6654595906:AAEg185xtzk03m2wz9cjH_oimfuI7idGOfg"


class TelegramHandler:
    
    def __init__(
        self,
        chat_id,
        bot_token=BOT_TOKEN,
        use_telegram=True,
    ):
        
        self.chat_id = chat_id
        self.use_telegram = use_telegram

        self.bot_token = bot_token

        self.__initialize_bot()
        
    def __initialize_bot(self):

        self.__bot = telebot.TeleBot(token=self.bot_token, threaded=False)
        
    def send_message(self, message, reply_markup):

        # self.__initialize_bot()
        
        try:
        
            message = self.__bot.send_message(self.chat_id, message, parse_mode='Markdown', reply_markup=reply_markup)

            # self.__bot.stop_bot()

            return message
            
        except telebot.apihelper.ApiTelegramException as e:
            
            try:
            
                seconds_to_sleep = int(str(e).split()[-1])
                
            except ValueError:
                
                seconds_to_sleep = 60
                
            time.sleep(seconds_to_sleep)
            
            return self.send_message(message, reply_markup)

    def send_file(self, path_to_file):

        # self.__initialize_bot()

        self.__bot.send_document(self.chat_id, path_to_file.open('rb'))

        # self.__bot.stop_bot()

    def __ask(self, message):

        # self.__initialize_bot()

        answer = ""

        def __answer(reply_message):

            nonlocal answer
            answer = reply_message.text

            self.__bot.stop_polling()
            # self.__bot.stop_bot()

        markup = types.ForceReply(selective=False)

        message_obj = self.send_message(message, reply_markup=markup)

        self.__bot.register_for_reply(message_obj, __answer)

        self.__bot.polling()

        if answer in ['stop', 'Stop', 's', 'S']:

            self.log_info("Algorithm is stopped!")

            raise KeyboardInterrupt

        return answer

    def log_info(
        self,
        message,
    ):

        print(message, end='\n\n', flush=True)

        if self.use_telegram:
            self.send_message(message, reply_markup=types.ReplyKeyboardRemove(selective=False))

    def ask_for_input(
        self,
        message
    ):

        if self.use_telegram:

            print("Answer the question on Telegram now!", end='\n\n', flush=True)

            return self.__ask(message)

        answer = input(message + "\n")
        print(flush=True)

        return answer

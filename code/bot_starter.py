import traceback
import telebot

from pathlib import Path
from datetime import datetime

from telegram_handler import TelegramHandler, BOT_TOKEN
from pipeline import Pipeline


max_n_users = 10
cur_n_users = 0

bot = telebot.TeleBot(token=BOT_TOKEN, threaded=True, num_threads=(max_n_users + 1))


@bot.message_handler(commands=['help'])
def handle_help(message):

    bot.reply_to(message, "Type /start to launch the algorithm!")


@bot.message_handler(commands=['start'])
def handle_start(message):

    global cur_n_users

    if cur_n_users >= max_n_users:

        bot.reply_to(message, f"Bot is busy! Current number of users is {cur_n_users}! Try again later!")

    else:

        cur_n_users += 1

        user_token = message.from_user.id

        use_telegram = True  # for debug

        logon_before_parsing = False
        headless = False

        telegram_handler = TelegramHandler(chat_id=user_token, use_telegram=use_telegram, bot=bot)

        try:

            telegram_handler.log_info("\nHello! Algorithm is started!")

            cur_button_list = [1, 2, 3]

            answer = telegram_handler.ask_for_input("How many ___days___ do you want me to optimize?", cur_button_list)

            while True:

                if answer in ["1", "2", "3"]:

                    n_days = int(answer)

                    break

                answer = telegram_handler.ask_for_input("Try again!", cur_button_list)

            data_filename = Path(Path(__file__).parent, "..", "data", "dishlist.xlsx")

            modification_time = datetime.fromtimestamp(data_filename.stat().st_mtime).strftime('%Y-%m-%d %H:%M')

            telegram_handler.log_info(f"Last time dish list was updated is {modification_time}")

            if Path(Path(__file__).parent, "..", "output", f"{user_token}.csv").exists():

                cur_button_list = ["full mode", "npq mode", "not parse"]

                answer = telegram_handler.ask_for_input(
                    "Do you want me to parse in ___full mode___ or ___npq mode___, or ___not parse___ at all?",
                    cur_button_list
                )

                while True:

                    if answer == "full mode":

                        parse_npq_only = False
                        use_parser = True

                        break

                    elif answer == "npq mode":

                        parse_npq_only = True
                        use_parser = True

                        break

                    elif answer == "not parse":

                        parse_npq_only = None
                        use_parser = False

                        break

                    answer = telegram_handler.ask_for_input("Try again!", cur_button_list)

            else:

                cur_button_list = ["full mode", "npq mode"]

                answer = telegram_handler.ask_for_input(
                    "You have not parsed VkusVill even once! "
                    "Do you want me to parse in ___full mode___ or ___npq mode___?",
                    cur_button_list
                )

                while True:

                    if answer == "full mode":

                        parse_npq_only = False
                        use_parser = True

                        break

                    elif answer == "npq mode":

                        parse_npq_only = True
                        use_parser = True

                        break

                    answer = telegram_handler.ask_for_input("Try again!", cur_button_list)

            Pipeline(
                n_days=n_days,
                user_token=user_token,
                use_parser=use_parser,
                parse_npq_only=parse_npq_only,
                use_telegram=use_telegram,
                logon_before_parsing=logon_before_parsing,
                headless=headless,
                telegram_handler=telegram_handler,
            ).run()

        except (Exception, KeyboardInterrupt):

            tb = traceback.format_exc()

            telegram_handler.log_info(f"```python\n{tb}```")

        cur_n_users -= 1


if __name__ == "__main__":

    bot.infinity_polling()

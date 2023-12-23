import json
import traceback

from pathlib import Path
from time import time

from telegram_handler import TelegramHandler
from optimizer import Optimizer
from parser import Parser
from utils import get_input_option


class Pipeline:

    def __init__(
        self,
        n_days,
        user_token,
        use_parser,
        parse_npq_only,
        use_telegram,
        logon_before_parsing,
        headless,
    ):

        self.n_days = n_days

        self.use_parser = use_parser
        self.parse_npq_only = parse_npq_only

        self.user_token = user_token

        self.use_telegram = use_telegram

        self.logon_before_parsing = logon_before_parsing
        self.headless = headless

        self.__initialize_telegram_handler()
        self.__initialize_config()
        self.__initialize_food_restrictions()
        self.__initialize_parser()
        self.__initialize_optimizer()

    def __initialize_telegram_handler(self):

        self.telegram_handler = TelegramHandler(
            chat_id=self.user_token,
            use_telegram=self.use_telegram
        )

    def __initialize_config(self):

        self.config = json.load(
            Path(Path(__file__).parents[0], "..", "config", f"{self.user_token}.json").open(encoding="utf-8"),
        )

    def __initialize_food_restrictions(self):

        self.food_restrictions = self.config["food_restrictions"]

    def __initialize_parser(self):

        address, _ = get_input_option(
            self.telegram_handler,
            "address",
            self.config["addresses"]
        )

        phone_number, _ = get_input_option(
            self.telegram_handler,
            "phone number",
            self.config["phone_numbers"]
        )

        self.parser = Parser(
            address=address,
            phone_number=phone_number,
            parse_npq_only=self.parse_npq_only,
            user_token=self.user_token,
            n_days=self.n_days,
            telegram_handler=self.telegram_handler,
            max_mass=self.config["max_mass"],
            logon_before_parsing=self.logon_before_parsing,
            headless=self.headless
        )

    def __initialize_optimizer(self):

        self.optimizer = Optimizer(
            telegram_handler=self.telegram_handler,
            n_days=self.n_days,
            calories_lower=self.food_restrictions["calories_lower"],
            calories_upper=self.food_restrictions["calories_upper"],
            proteins_lower=self.food_restrictions["proteins_lower"],
            proteins_upper=self.food_restrictions["proteins_upper"],
            fats_lower=self.food_restrictions["fats_lower"],
            fats_upper=self.food_restrictions["fats_upper"],
            carbo_lower=self.food_restrictions["carbo_lower"],
            carbo_upper=self.food_restrictions["carbo_upper"],
            start_min_price=self.config["start_min_price"],
            parser=self.parser
        )

    def run(self):

        if self.use_parser:

            self.telegram_handler.log_info("Started parsing")

            start_time = time()

            self.parser.parse_data(
                links=None,
                save_to_csv=True,
            )

            self.telegram_handler.log_info(f"Finished parsing: {time() - start_time:.2f} sec")

        self.telegram_handler.log_info("Started filtering data")

        start_time = time()

        self.parser.get_and_filter_data()

        self.telegram_handler.log_info(f"Finished filtering data: {time() - start_time:.2f} sec")

        self.telegram_handler.log_info("Started optimizing")

        start_time = time()

        food_dict = self.optimizer.launch_optimizer(food_df=self.parser.food_df)

        self.telegram_handler.log_info(f"Finished optimizing: {time() - start_time:.2f} sec")

        self.telegram_handler.log_info("Started adding to cart")

        start_time = time()

        self.parser.launch_cart(
            self.optimizer.min_dict_list,
            food_dict,
        )

        self.telegram_handler.log_info(f"Finished adding to cart: {time() - start_time:.2f} sec")

        self.telegram_handler.log_info("Algorithm is finished! Bye-bye!")


if __name__ == '__main__':

    global_user_token = 138619108
    global_use_parser = False

    global_use_telegram = True

    global_logon_before_parsing = False
    global_headless = False

    telegram_handler = TelegramHandler(chat_id=global_user_token, use_telegram=global_use_telegram)

    try:

        telegram_handler.log_info("\nHello! Algorithm is started!")

        answer = telegram_handler.ask_for_input("How many days do you want me to optimize? (1/2/3)")

        while True:

            if answer in ["1", "2", "3"]:

                global_n_days = int(answer)

                break

            answer = telegram_handler.ask_for_input("Try again: 1/2/3")

        answer = telegram_handler.ask_for_input("Do you want me to parse in full mode or npq mode? (full/npq)")

        while True:

            if answer == "full":

                global_parse_npq_only = False

                break

            elif answer == "npq":

                global_parse_npq_only = True

                break

            answer = telegram_handler.ask_for_input("Try again: full/npq")

        Pipeline(
            n_days=global_n_days,
            user_token=global_user_token,
            use_parser=global_use_parser,
            parse_npq_only=global_parse_npq_only,
            use_telegram=global_use_telegram,
            logon_before_parsing=global_logon_before_parsing,
            headless=global_headless,
        ).run()

    except (Exception, KeyboardInterrupt) as exception:

        tb = traceback.format_exc()

        telegram_handler.log_info(f"```python\n{tb}```")

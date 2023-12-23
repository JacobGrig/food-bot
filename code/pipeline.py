import json
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
        telegram_handler,
    ):

        self.n_days = n_days

        self.use_parser = use_parser
        self.parse_npq_only = parse_npq_only

        self.user_token = user_token

        self.use_telegram = use_telegram

        self.logon_before_parsing = logon_before_parsing
        self.headless = headless

        self.config = {"food_restrictions": {}}

        if telegram_handler is not None:
            self.telegram_handler = telegram_handler
        else:
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

        config_path = Path(Path(__file__).parent, "..", "config", f"{self.user_token}.json")

        if not config_path.exists():

            self.__change_config()

            json.dump(
                self.config,
                config_path.open('w', encoding="utf-8"),
                ensure_ascii=False,
                indent=2
            )

        else:

            self.config = json.load(config_path.open(encoding="utf-8"))

            self.__print_config()

            while True:

                change_section, _ = get_input_option(
                    self.telegram_handler,
                    "part of the config you want to change",
                    [
                        "addresses (append)",
                        "addresses (new)",
                        "phone numbers (append)",
                        "phone numbers (new)",
                        "lower bound for calories",
                        "upper bound for calories",
                        "lower bound for proteins",
                        "upper bound for proteins",
                        "lower bound for fats",
                        "upper bound for fats",
                        "lower bound for carbohydrates",
                        "upper bound for carbohydrates",
                        "maximum mass of one dish",
                        "maximum price for daily set",
                        "nothing"
                    ]
                )

                match change_section:

                    case "nothing": break

                    case "addresses (append)": self.__change_addresses(True)
                    case "addresses (new)": self.__change_addresses(False)

                    case "phone numbers (append)": self.__change_phone_numbers(True)
                    case "phone numbers (new)": self.__change_phone_numbers(False)

                    case "lower bound for calories": self.__change_calories_lower()
                    case "upper bound for calories": self.__change_calories_upper()

                    case "lower bound for proteins": self.__change_proteins_lower()
                    case "upper bound for proteins": self.__change_proteins_upper()

                    case "lower bound for fats": self.__change_fats_lower()
                    case "upper bound for fats": self.__change_fats_upper()

                    case "lower bound for carbohydrates": self.__change_carbo_lower()
                    case "upper bound for carbohydrates": self.__change_carbo_upper()

                    case "maximum mass of one dish": self.__change_max_mass()
                    case "maximum price for daily set": self.__change_start_min_price()

                self.__print_config()

            json.dump(
                self.config,
                config_path.open('w', encoding="utf-8"),
                ensure_ascii=False,
                indent=2
            )

    def __change_multiple_values(self, name, names, key, example, append):

        value = self.telegram_handler.ask_for_input(
            f"Enter your ___{name}___ (e.g. {example})",
            button_list=None
        )

        value_list = [value, ]

        while True:

            answer = self.telegram_handler.ask_for_input(
                f"Do you want me to save ___more {names}___?",
                button_list=["yes", "no"]
            )

            should_break = False

            while True:

                if answer == "yes":

                    value = self.telegram_handler.ask_for_input(
                        f"Enter your ___{name}___ (e.g. {example})",
                        button_list=None
                    )

                    value_list.append(value)

                    break

                elif answer == "no":

                    should_break = True

                    break

                else:

                    answer = self.telegram_handler.ask_for_input("Try again!", button_list=["yes", "no"])

            if should_break:
                break

        if append:

            self.config[key].append(value_list)

        else:

            self.config[key] = value_list

    def __change_addresses(self, append):

        self.__change_multiple_values(
            name="address",
            names="addresses",
            key="addresses",
            example="Москва, Самокатная улица, 6к1",
            append=append
        )

    def __change_phone_numbers(self, append):

        self.__change_multiple_values(
            name="phone number",
            names="phone numbers",
            key="phone_numbers",
            example=9057585915,
            append=append
        )

    def __change_value(self, name, key, example, bound):

        value = self.telegram_handler.ask_for_input(
            f"Enter ___{name}___ (e.g. {example})",
            button_list=None
        )

        while True:

            try:

                value = int(value)

                if value <= 0:
                    raise ValueError

                if bound == "upper":

                    if value <= self.config["food_restrictions"][key.replace("upper", "lower")]:
                        raise ValueError

                break

            except ValueError:

                value = self.telegram_handler.ask_for_input(
                    "You should enter positive integer number!",
                    button_list=None
                )

        self.config["food_restrictions"][key] = value

    def __change_calories_lower(self):

        self.__change_value(name="lower bound for calories", key="calories_lower", example=2000, bound="lower")

    def __change_calories_upper(self):

        self.__change_value(name="upper bound for calories", key="calories_upper", example=2500, bound="upper")

    def __change_proteins_lower(self):

        self.__change_value(name="lower bound for proteins", key="proteins_lower", example=150, bound="lower")

    def __change_proteins_upper(self):

        self.__change_value(name="upper bound for proteins", key="proteins_upper", example=250, bound="upper")

    def __change_fats_lower(self):

        self.__change_value(name="lower bound for fats", key="fats_lower", example=50, bound="lower")

    def __change_fats_upper(self):

        self.__change_value(name="upper bound for fats", key="fats_upper", example=150, bound="upper")

    def __change_carbo_lower(self):

        self.__change_value(name="lower bound for carbohydrates", key="carbo_lower", example=200, bound="lower")

    def __change_carbo_upper(self):

        self.__change_value(name="upper bound for carbohydrates", key="carbo_upper", example=300, bound="upper")

    def __change_max_mass(self):

        self.__change_value(name="maximum mass of one dish", key="max_mass", example=300, bound="")

    def __change_start_min_price(self):

        self.__change_value(name="maximum price of daily set", key="start_min_price", example=1500, bound="")

    def __change_config(self):

        self.__change_addresses(False)
        self.__change_phone_numbers(False)
        self.__change_calories_lower()
        self.__change_calories_upper()
        self.__change_proteins_lower()
        self.__change_proteins_upper()
        self.__change_fats_lower()
        self.__change_fats_upper()
        self.__change_carbo_lower()
        self.__change_carbo_upper()
        self.__change_max_mass()
        self.__change_start_min_price()

    def __print_config(self):

        addresses_str = "\n".join([f"    {i}. {address}" for i, address in enumerate(self.config["addresses"])])

        phone_numbers_str = "\n".join(
            [f"    {i}. {phone_number}" for i, phone_number in enumerate(self.config["phone_numbers"])]
        )

        print_str = f"""
***Current config***:

___addresses___: \n{addresses_str}

___phone numbers___: \n{phone_numbers_str}

___lower bound for calories___: {self.config["food_restrictions"]["calories_lower"]}
___upper bound for calories___: {self.config["food_restrictions"]["calories_upper"]}

___lower bound for proteins___: {self.config["food_restrictions"]["proteins_lower"]}
___upper bound for proteins___: {self.config["food_restrictions"]["proteins_upper"]}

___lower bound for fats___: {self.config["food_restrictions"]["fats_lower"]}
___upper bound for fats___: {self.config["food_restrictions"]["fats_upper"]}

___lower bound for carbohydrates___: {self.config["food_restrictions"]["carbo_lower"]}
___upper bound for carbohydrates___: {self.config["food_restrictions"]["carbo_upper"]}

___maximum mass of one dish___: {self.config["food_restrictions"]["max_mass"]}
___maximum price for daily set___: {self.config["food_restrictions"]["start_min_price"]}
        """

        self.telegram_handler.log_info(print_str)

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
            max_mass=self.food_restrictions["max_mass"],
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
            start_min_price=self.food_restrictions["start_min_price"],
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

        # self.telegram_handler.log_info("Started adding to cart")
        #
        # start_time = time()
        #
        # self.parser.launch_cart(
        #     self.optimizer.min_dict_list,
        #     food_dict,
        # )
        #
        # self.telegram_handler.log_info(f"Finished adding to cart: {time() - start_time:.2f} sec")

        self.telegram_handler.log_info("Algorithm is finished! Bye-bye!")

        # self.telegram_handler.stop_bot()

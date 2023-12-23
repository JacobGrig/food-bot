import re
import time

import numpy as np
import pandas as pd

from pathlib import Path
from typing import Optional, Tuple

from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotInteractableException

from webdriver_manager.chrome import ChromeDriverManager

from utils import get_input_option


class Parser:

    SECTION_LINK = "https://rtw.vkusvill.ru/goods/gotovaya-eda/"
    DATA_FILENAME = "dishlist.xlsx"
    WAIT_TIMEOUT = 10
    SLEEP_AFTER_WAIT = 2

    def __init__(
        self,
        address,
        phone_number,
        parse_npq_only,
        user_token,
        n_days,
        telegram_handler,
        max_mass,
        logon_before_parsing,
        headless
    ):

        self.address = address
        self.delivery_interval = None

        self.phone_number = phone_number

        self.parse_npq_only = parse_npq_only

        self.user_token = user_token

        self.n_days = n_days

        self.telegram_handler = telegram_handler

        self.max_mass = max_mass

        self.logon_before_parsing = logon_before_parsing
        self.headless = headless

        self.__initialize_driver()

    def __initialize_driver(self):

        service = Service(ChromeDriverManager().install())
        options = Options()

        if self.headless:

            options.add_argument('--headless=new')

            driver = webdriver.Chrome(service=service, options=options)

            user_agent = driver.execute_script("return navigator.userAgent")

            driver.quit()

            options.add_argument(f'user-agent={user_agent.replace("Headless", "")}')

        self.driver = webdriver.Chrome(service=service, options=options)

        self.driver.set_window_size(1200, 800)

        self.driver.get("https://vkusvill.ru/")

        if self.logon_before_parsing:

            self.__log_in()

        self.delivery_interval = self.__set_address_and_delivery_interval()

    def __set_address_and_delivery_interval(self):

        button = self.driver.find_element(
            By.CSS_SELECTOR,
            "span[class*='HeaderATDToggler__Text rtext _desktop-md _tablet-sm _mobile-sm']",
        )

        self.driver.execute_script("arguments[0].scrollIntoView();", button)
        self.driver.execute_script("arguments[0].click();", button)

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, ".VV23_RWayModal_Main__Form._delivery")
            )
        )

        time.sleep(self.SLEEP_AFTER_WAIT)

        address_area = self.driver.find_element(
            By.CSS_SELECTOR, ".VV23_RWayModal_Main__Form._delivery"
        )

        text_area = address_area.find_element(
            By.CSS_SELECTOR, ".VV_Input__Input.js-vv-control__input"
        )

        text_area.send_keys(" ")

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, "VV_Input__Clear")
            )
        )

        time.sleep(self.SLEEP_AFTER_WAIT)

        clear_button = address_area.find_element(
            By.CLASS_NAME, "VV_Input__Clear"
        )

        self.driver.execute_script("arguments[0].click();", clear_button)

        time.sleep(self.SLEEP_AFTER_WAIT)

        text_area.send_keys(self.address)

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, ".VV_Dropdown__option.js-suggest")
            )
        )

        time.sleep(self.SLEEP_AFTER_WAIT)

        dropdown_button_cand_list = self.driver.find_elements(
            By.CSS_SELECTOR, ".VV_Dropdown__option.js-suggest"
        )

        dropdown_button = None

        for dropdown_button in dropdown_button_cand_list:

            if dropdown_button.text != '':
                break

        self.driver.execute_script("arguments[0].click();", dropdown_button)

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, ".VV_Button._desktop-lg._tablet-md._mobile-md._block")
            )
        )

        time.sleep(self.SLEEP_AFTER_WAIT)

        deliver_button = self.driver.find_element(
            By.CSS_SELECTOR, ".VV_Button._desktop-lg._tablet-md._mobile-md._block"
        )

        self.driver.execute_script("arguments[0].click();", deliver_button)

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, ".VV_Radio._separ._circleRight")
            )
        )

        time.sleep(self.WAIT_TIMEOUT)

        delivery_interval_cand_list = self.driver.find_elements(
            By.CSS_SELECTOR, ".VV_Radio._separ._circleRight"
        )

        if self.delivery_interval is not None:

            delivery_interval_text = self.delivery_interval

            delivery_interval_button = None

            for delivery_interval_button in delivery_interval_cand_list:

                if delivery_interval_button.text == self.delivery_interval:
                    break

        else:

            delivery_interval_list = []
            index_list = []

            for index, delivery_interval_button in enumerate(delivery_interval_cand_list):

                cur_text = delivery_interval_button.text

                if cur_text != '':

                    index_list.append(index)

                    delivery_interval_list.append(delivery_interval_button.text)

            delivery_interval_text, delivery_interval_index = get_input_option(
                self.telegram_handler,
                "delivery interval",
                delivery_interval_list
            )

            delivery_interval_button = delivery_interval_cand_list[index_list[delivery_interval_index]]

        self.driver.execute_script("arguments[0].scrollIntoView();", delivery_interval_button)
        delivery_interval_button.click()

        time.sleep(self.WAIT_TIMEOUT)

        return delivery_interval_text

    def parse_data(
        self,
        links,
        save_to_csv,
        parse_npq_only=None
    ):

        if parse_npq_only is None:
            parse_npq_only = self.parse_npq_only

        out = []

        if not parse_npq_only:

            if links is None:

                links = self.__get_product_links(self.SECTION_LINK)

            for link in links:

                product_card = self.__get_product_card(link)

                if product_card:
                    out.append(product_card)

        else:

            out += self.__parse_npq_for_section(self.SECTION_LINK)

        if save_to_csv:

            self.__save_data_to_csv(
                out,
                Path(Path(__file__).parents[0], "..", "output", f"{self.user_token}.csv")
            )

        else:

            return out

    def __parse_npq_for_section(
        self,
        section_link: str
    ) -> list:

        self.driver.get(section_link)

        out = []

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, "ProductCard__content"))
        )

        name_set = set()

        while True:

            forward = self.driver.find_elements(By.LINK_TEXT, "Вперёд")

            product_cards = self.driver.find_element(
                By.CSS_SELECTOR, ".Catalog__col.Catalog__col--main"
            ).find_elements(
                By.CLASS_NAME,
                "ProductCard__content"
            )

            driver_copy = self.driver

            for product_card in product_cards:

                self.driver = product_card

                cur_name = self.__get_product_name(link=None, from_product_card=True)

                if cur_name in name_set:
                    continue

                name_set.add(cur_name)

                cur_price = self.__get_price()
                cur_quantity = self.__get_quantity(from_product_card=True)

                out.append(
                    {
                        'name': cur_name,
                        'price': cur_price,
                        'quantity': cur_quantity,
                    }
                )

            self.driver = driver_copy

            if not forward:
                return out

            self.driver.get(forward[0].get_attribute("href"))

            WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                expected_conditions.presence_of_element_located(
                    (By.CLASS_NAME, "ProductCard__content")
                )
            )

    def __get_product_links(
        self,
        link
    ) -> set:

        links = set()

        self.driver.get(link)

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, "ProductCard__image"))
        )

        while True:

            forward = self.driver.find_elements(By.LINK_TEXT, "Вперёд")

            product_cards = self.driver.find_element(
                By.CSS_SELECTOR, ".Catalog__col.Catalog__col--main"
            ).find_elements(
                By.CLASS_NAME,
                "ProductCard__image"
            )

            for product_card in product_cards:
                links.add(
                    product_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                )

            if not forward:
                return links

            self.driver.get(forward[0].get_attribute("href"))

            WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                expected_conditions.presence_of_element_located(
                    (By.CLASS_NAME, "ProductCard__image")
                )
            )

    def __get_product_name(
        self,
        link: Optional[str],
        from_product_card
    ) -> str:

        if link is not None:
            self.driver.get(link)

        if not from_product_card:

            WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                expected_conditions.presence_of_element_located((By.CLASS_NAME, "Product__title"))
            )

            elem_list = self.driver.find_elements(By.CLASS_NAME, "Product__title")

        else:

            WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                expected_conditions.presence_of_element_located((By.TAG_NAME, "a"))
            )

            elem_list = self.driver.find_elements(By.TAG_NAME, "a")

        for elem in elem_list:

            cur_text = elem.text

            if cur_text != "":

                return cur_text

        return ""

    @staticmethod
    def __convert_to_grams(
        quantity: str
    ) -> Optional[int]:

        pattern = r"(\d+(?:[,.]\d+)?)\s*(г|кг|мл|л)"
        match = re.match(pattern, quantity)

        if match:

            value = float(match.group(1).replace(",", "."))
            unit = match.group(2).lower()

            return (
                int(value * 1000)
                if unit in ["кг", "л"]
                else int(value)
            )

        else:

            return None

    def __get_mass(
        self
    ) -> Optional[int]:

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, "div[class*='ProductCard__weight']")
            )
        )

        mass = self.driver.find_element(By.CSS_SELECTOR, "div[class*='ProductCard__weight']").text

        mass = self.__convert_to_grams(mass)

        return mass

    def __get_price(
        self,
    ) -> str:

        elem_list = self.driver.find_elements(By.CLASS_NAME, "Price__value")

        for elem in elem_list:

            cur_text = elem.text

            if cur_text != "":
                return cur_text

        return ""

    def __get_nutritional_value(
        self
    ) -> str:

        try:

            elem_to_wait = ".Product__details-text"

            WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                expected_conditions.presence_of_element_located((
                    By.CSS_SELECTOR, elem_to_wait
                ))
            )

            elem_list = self.driver.find_elements(
                By.CSS_SELECTOR, elem_to_wait
            )

            for elem in elem_list:

                cur_text = elem.text

                if cur_text != "":
                    return cur_text

            return ""

        except TimeoutException:

            try:

                elem_to_wait = ".VV23_DetailProdPageInfoDescItem"

                WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                    expected_conditions.presence_of_element_located((
                        By.CSS_SELECTOR, elem_to_wait
                    ))
                )

                elem_list = self.driver.find_elements(
                    By.CSS_SELECTOR, elem_to_wait
                )

                for elem in elem_list:

                    cur_text_list = elem.text.split('\n')

                    if cur_text_list[0] == 'Пищевая и энергетическая ценность в 100 г.':
                        return cur_text_list[1]

                return ""

            except TimeoutException:

                return ""

    @staticmethod
    def __extract_nutritional_info(nutritional_value: str) -> Tuple:

        pattern = r"[бБ]елки\s?(\d+(?:[,.]\d+)?)\s?(?:г)?[;,.]?\s?" \
                  r"жиры\s?(\d+(?:[,.]\d*)?)\s?(?:г)?[;,.]?\s?" \
                  r"углеводы\s?(\d+(?:[,.]\d+)?)\s?(?:г)?[;,.]?\s?" \
                  r"(\d+(?:[,.]\d*)?)\s?ккал"

        matches = re.match(pattern, nutritional_value)

        if matches:

            proteins = matches.group(1).replace(",", ".")
            fats = matches.group(2).replace(",", ".")
            carbohydrates = matches.group(3).replace(",", ".")
            calories = matches.group(4).replace(",", ".")

            return proteins, fats, carbohydrates, calories

        else:

            return None, None, None, None

    @staticmethod
    def __get_cart_text(
        product_card
    ) -> str:

        elem_list = product_card.find_elements(
            By.CLASS_NAME,
            "CartButton__inner"
        )

        for elem in elem_list:

            cur_text = elem.text

            if cur_text != "":

                return cur_text

        return ""

    def __get_quantity(
        self,
        from_product_card
    ) -> int:

        elem_list = self.driver.find_elements(
            By.CSS_SELECTOR,
            (
                "div[class*='ProductLkRest rtext']"
                if not from_product_card
                else "div[class*='ProductCard__Rest caption']"
            )
        )

        for elem in elem_list:

            cur_text = elem.text

            if cur_text != "":

                quantity = cur_text

                break

        else:

            quantity = ""

        cart_text = self.__get_cart_text(self.driver)

        if ("В наличии" in quantity) and (
            (cart_text == "В корзину") or re.match(r"\d+ шт\d+руб", cart_text.replace("\n", ""))
        ):

            matches = re.search(r"\d+", quantity.replace(" ", ""))

            if matches:
                return int(matches.group())

        return 0

    def __get_product_card(
        self,
        link: str
    ) -> Optional[dict]:

        card = {}

        try:

            card["name"] = self.__get_product_name(link, from_product_card=False)
            card["mass"] = self.__get_mass()
            card["quantity"] = self.__get_quantity(from_product_card=False)
            card["price"] = self.__get_price()

            nutritional_value = self.__get_nutritional_value()
            nutritional_info = self.__extract_nutritional_info(nutritional_value)

            (
                card["proteins"],
                card["fats"],
                card["carbohydrates"],
                card["calories"],
            ) = nutritional_info

            card["link"] = link

        except Exception as e:

            self.telegram_handler.log_info(f"An error {e} occurred while fetching product info for {link}")

            return None

        return card

    @staticmethod
    def __save_data_to_csv(
        data_strings,
        filename
    ):

        df = pd.DataFrame(data_strings)
        df.to_csv(filename, index=False, encoding="utf-8")

    def __log_in(
        self,
    ):

        self.driver.get("https://vkusvill.ru/personal/")

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR,
                 ".VV_Input__Input.js-vv-control__input.js-input-mask-phone.js-user-form-checksms-api-phone1")
            )
        )

        time.sleep(self.SLEEP_AFTER_WAIT)

        phone_form = self.driver.find_element(
            By.CSS_SELECTOR,
            ".VV_Input__Input.js-vv-control__input.js-input-mask-phone.js-user-form-checksms-api-phone1"
        )

        phone_form.send_keys(self.phone_number)

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, ".VV_Button._desktop-lg._tablet-lg._mobile-md._block.js-user-form-submit-btn")
            )
        )

        time.sleep(self.SLEEP_AFTER_WAIT)

        continue_button = self.driver.find_element(
            By.CSS_SELECTOR, ".VV_Button._desktop-lg._tablet-lg._mobile-md._block.js-user-form-submit-btn"
        )

        self.driver.execute_script("arguments[0].click();", continue_button)

        WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR,
                 ".VV_Input__Input.js-vv-control__input.js-input-mask-phone.js-user-form-checksms-api-sms")
            )
        )

        time.sleep(self.SLEEP_AFTER_WAIT)

        sms_form = self.driver.find_element(
            By.CSS_SELECTOR,
            ".VV_Input__Input.js-vv-control__input.js-input-mask-phone.js-user-form-checksms-api-sms"
        )

        sms_code = self.telegram_handler.ask_for_input("Insert your SMS-code here: ")

        sms_form.send_keys(sms_code)

        time.sleep(self.WAIT_TIMEOUT)

    def __read_and_convert_data(self):

        food_df = pd.read_csv(
            Path(Path(__file__).parents[0], "..", "output", f"{self.user_token}.csv"),
            encoding="utf-8",
            delimiter=",",
            index_col="name",
            dtype=str
        )

        food_df["price"] = food_df["price"] \
            .str.replace(" ", "") \
            .astype(np.float64)

        food_df["quantity"] = food_df["quantity"] \
            .str.replace(" ", "") \
            .astype(np.float64).astype(np.int32)

        if not self.parse_npq_only:
            food_df["calories"] = food_df["calories"] \
                .str.replace(" ", "") \
                .astype(np.float64)

            food_df["proteins"] = food_df["proteins"] \
                .str.replace(" ", "") \
                .astype(np.float64)

            food_df["fats"] = food_df["fats"] \
                .str.replace(" ", "") \
                .astype(np.float64)

            food_df["carbohydrates"] = food_df["carbohydrates"] \
                .str.replace(" ", "") \
                .astype(np.float64)

            food_df["mass"] = food_df["mass"] \
                .str.replace(" ", "") \
                .astype(np.float64)

        self.food_df = food_df

    def __update_dishlist(self):

        path_to_file = Path(Path(__file__).parents[0], "..", "data", "dishlist.xlsx")

        if self.parse_npq_only:

            dishlist_df = pd.read_excel(path_to_file, index_col='name')

            dishlist_df = dishlist_df.loc[~dishlist_df.index.duplicated()]

            self.food_df = self.food_df.merge(
                dishlist_df,
                how='left',
                left_index=True,
                right_index=True
            )

        self.food_df = self.food_df.dropna(
            subset=["calories", "proteins", "fats", "carbohydrates", "mass"]
        )

        self.food_df.drop(columns=["quantity", "price"]).sort_index().to_excel(path_to_file)

    def __filter_by_mass(self):

        self.food_df["final_quantity"] = np.minimum(
            self.food_df["quantity"],
            self.max_mass // self.food_df["mass"]
        )

        self.food_df["calories"] = self.food_df["calories"] * self.food_df["mass"] / 100
        self.food_df["proteins"] = self.food_df["proteins"] * self.food_df["mass"] / 100
        self.food_df["fats"] = self.food_df["fats"] * self.food_df["mass"] / 100
        self.food_df["carbo"] = self.food_df["carbohydrates"] * self.food_df["mass"] / 100

        self.food_df = self.food_df[[
            "price",
            "calories",
            "proteins",
            "fats",
            "carbo",
            "final_quantity",
            "link",
            "mass"
        ]].rename(columns={"final_quantity": "quantity"})

        self.food_df = self.food_df.loc[self.food_df["quantity"] > 0]

    def get_and_filter_data(self):

        self.__read_and_convert_data()
        self.__update_dishlist()
        self.__filter_by_mass()

    def launch_cart(
        self,
        min_dict_list,
        food_dict,
    ):

        final_dict = {}

        for min_dict in min_dict_list:
            cur_dict = {
                food_dict[name]["link"]: quantity
                for name, quantity in min_dict.items()
            }

            final_dict.update(cur_dict)

        self.__add_products_to_cart(final_dict)

    def __add_products_to_cart(
        self,
        data,
    ):

        if not self.logon_before_parsing:

            self.__log_in()
            self.delivery_interval = self.__set_address_and_delivery_interval()

        for link in data:
            self.__add_product_to_cart(link, data[link])

        self.telegram_handler.log_info("Everything is ready! Go to your cart and order now!")

    def __add_product_to_cart(
        self,
        link: str,
        req_quantity: int,
    ):

        self.driver.get(link)
        available_quantity = min(req_quantity, self.__get_quantity(from_product_card=False))

        if available_quantity:

            WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     "button[class*='CartButton__content CartButton__content--add js-delivery__basket--add']")
                )
            )

            time.sleep(self.SLEEP_AFTER_WAIT)

            for button in self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[class*='CartButton__content CartButton__content--add js-delivery__basket--add']",
            ):

                if button.text == 'В корзину':

                    self.driver.execute_script("arguments[0].scrollIntoView();", button)
                    self.driver.execute_script("arguments[0].click();", button)

            if available_quantity > 1:

                WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR,
                         ".CartButton__quantityButton.js-delivery__product__q-btn.Q_Up")
                    )
                )

                time.sleep(self.SLEEP_AFTER_WAIT)

                for plus_button in self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".CartButton__quantityButton.js-delivery__product__q-btn.Q_Up",
                ):

                    for _ in range(available_quantity - 1):

                        already_full = False

                        for elem in self.driver.find_elements(
                            By.CSS_SELECTOR,
                            ".CartButton__quantityInputFake.js-delivery__product__qfake"
                        ):
                            cur_text = elem.text

                            if cur_text != "":

                                if int(cur_text) >= available_quantity:
                                    already_full = True

                                break

                        if already_full:
                            break

                        try:

                            self.driver.execute_script("arguments[0].scrollIntoView();", plus_button)
                            self.driver.execute_script("arguments[0].click();", plus_button)

                            time.sleep(self.SLEEP_AFTER_WAIT)

                        except ElementNotInteractableException:

                            self.telegram_handler.log_info(f"Plus button is not interactable at {link}")

                            break

        self.telegram_handler.log_info(f"{link} is added to cart")

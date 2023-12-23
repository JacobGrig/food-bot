import time

import numpy as np
import pandas as pd

from numpy.random import default_rng


class Optimizer:

    N_DISHES = 20
    MAX_ATTEMPTS = 100

    def __init__(
        self,
        telegram_handler,
        n_days,
        calories_lower,
        calories_upper,
        proteins_lower,
        proteins_upper,
        fats_lower,
        fats_upper,
        carbo_lower,
        carbo_upper,
        start_min_price,
        parser
    ):

        self.telegram_handler = telegram_handler

        self.n_days = n_days

        self.calories_lower = calories_lower
        self.calories_upper = calories_upper

        self.proteins_lower = proteins_lower
        self.proteins_upper = proteins_upper

        self.fats_lower = fats_lower
        self.fats_upper = fats_upper

        self.carbo_lower = carbo_lower
        self.carbo_upper = carbo_upper

        self.start_min_price = start_min_price

        self.parser = parser

        self.min_dict_list = None

    def launch_optimizer(self, food_df):

        min_dict_list = []
        min_price_list = []

        food_copy_df = food_df.copy()

        for i_day in range(self.n_days):

            cur_min_dict = None
            cur_min_price = None

            self.telegram_handler.log_info(f"Day {i_day + 1}")

            start_time = time.time()

            is_optimized = False

            n_attempts = 0

            while not is_optimized:

                cur_min_price = self.start_min_price

                cur_min_dict = None

                while cur_min_price == self.start_min_price:

                    self.telegram_handler.log_info(f"Attempt {n_attempts + 1}")

                    rng = default_rng()

                    size = food_df.index.size
                    number_vec = rng.choice(
                        size,
                        size=min(self.N_DISHES, size),
                        replace=False
                    )

                    sliced_food_df = food_df.iloc[number_vec]

                    calories_vec = sliced_food_df["calories"].values
                    proteins_vec = sliced_food_df["proteins"].values
                    fats_vec = sliced_food_df["fats"].values
                    carbo_vec = sliced_food_df["carbo"].values
                    price_vec = sliced_food_df["price"].values
                    quantity_vec = sliced_food_df["quantity"].astype(int).values

                    cur_price = 0

                    min_quantity_vec = np.zeros_like(quantity_vec)

                    rest_quantity_vec = quantity_vec.copy()

                    cur_min_quantity_vec, cur_min_price = self.__optimize(
                        0,
                        calories_vec,
                        proteins_vec,
                        fats_vec,
                        carbo_vec,
                        price_vec,
                        quantity_vec,
                        self.calories_lower,
                        self.calories_upper,
                        self.proteins_lower,
                        self.proteins_upper,
                        self.fats_lower,
                        self.fats_upper,
                        self.carbo_lower,
                        self.carbo_upper,
                        rest_quantity_vec,
                        cur_price,
                        min_quantity_vec,
                        self.start_min_price
                    )

                    cur_min_index = sliced_food_df[cur_min_quantity_vec > 0].index

                    cur_min_quantity_vec = cur_min_quantity_vec[cur_min_quantity_vec > 0]

                    cur_min_dict = pd.Series(cur_min_quantity_vec, index=cur_min_index).to_dict()

                    n_attempts += 1

                    if n_attempts >= self.MAX_ATTEMPTS:
                        self.telegram_handler.log_info(
                            'It is impossible to assemble a daily '
                            'food out of the rest products!'
                        )

                        break

                if n_attempts >= self.MAX_ATTEMPTS:
                    break

                self.min_dict_list = [cur_min_dict, ]

                self.__print_optimal_set_info(i_day, food_df)

                cur_button_list = ["yes", "no"]

                answer = self.telegram_handler.ask_for_input("Do you like your set?", cur_button_list)

                while True:

                    if answer == "yes":

                        is_optimized = True

                        break

                    if answer == "no":

                        break

                    answer = self.telegram_handler.ask_for_input("Try again!", cur_button_list)

            if n_attempts >= self.MAX_ATTEMPTS:
                break

            self.telegram_handler.log_info(f"Optimization finished for day {i_day + 1}!")

            min_dict_list.append(cur_min_dict)
            min_price_list.append(cur_min_price)

            food_df = food_df.drop(cur_min_dict.keys())

            self.telegram_handler.log_info(
                f"Time elapsed on day {i_day + 1}: {time.time() - start_time: .2f} sec"
            )

        food_df = food_copy_df
        
        self.min_dict_list = min_dict_list

        food_dict = self.__print_optimal_set_info(0, food_df)

        return food_dict

    @staticmethod
    def __optimize(
        i_first_dish,
        calories_vec,
        proteins_vec,
        fats_vec,
        carbo_vec,
        price_vec,
        quantity_vec,
        calories_lower,
        calories_upper,
        proteins_lower,
        proteins_upper,
        fats_lower,
        fats_upper,
        carbo_lower,
        carbo_upper,
        rest_quantity_vec,
        cur_price,
        min_quantity_vec,
        min_price,
    ):

        assert calories_upper >= 0
        assert proteins_upper >= 0
        assert fats_upper >= 0
        assert carbo_upper >= 0

        assert min_price > cur_price

        if (calories_lower <= 0) and \
           (proteins_lower <= 0) and \
           (fats_lower <= 0) and \
           (carbo_lower <= 0):

            return quantity_vec - rest_quantity_vec, cur_price

        elif i_first_dish == price_vec.size:

            return min_quantity_vec, min_price

        assert rest_quantity_vec[i_first_dish] > 0

        cur_calories = calories_vec[i_first_dish]
        cur_proteins = proteins_vec[i_first_dish]
        cur_fats = fats_vec[i_first_dish]
        cur_carbo = carbo_vec[i_first_dish]

        rest_modified = False
        first_dish_modified = False

        if (cur_calories <= calories_upper) and \
           (cur_proteins <= proteins_upper) and \
           (cur_fats <= fats_upper) and \
           (cur_carbo <= carbo_upper):

            new_cur_price = cur_price + price_vec[i_first_dish]

            if new_cur_price < min_price:

                rest_modified = True

                rest_quantity_vec[i_first_dish] -= 1

                if rest_quantity_vec[i_first_dish] == 0:

                    first_dish_modified = True

                    i_first_dish += 1

                min_quantity_vec, min_price = Optimizer.__optimize(
                    i_first_dish,
                    calories_vec,
                    proteins_vec,
                    fats_vec,
                    carbo_vec,
                    price_vec,
                    quantity_vec,
                    calories_lower - cur_calories,
                    calories_upper - cur_calories,
                    proteins_lower - cur_proteins,
                    proteins_upper - cur_proteins,
                    fats_lower - cur_fats,
                    fats_upper - cur_fats,
                    carbo_lower - cur_carbo,
                    carbo_upper - cur_carbo,
                    rest_quantity_vec,
                    new_cur_price,
                    min_quantity_vec,
                    min_price,
                )

        new_cur_price = cur_price

        if first_dish_modified:

            i_first_dish -= 1

        if rest_modified:

            rest_quantity_vec[i_first_dish] += 1

        i_first_dish += 1

        return Optimizer.__optimize(
            i_first_dish,
            calories_vec,
            proteins_vec,
            fats_vec,
            carbo_vec,
            price_vec,
            quantity_vec,
            calories_lower,
            calories_upper,
            proteins_lower,
            proteins_upper,
            fats_lower,
            fats_upper,
            carbo_lower,
            carbo_upper,
            rest_quantity_vec,
            new_cur_price,
            min_quantity_vec,
            min_price,
        )

    def __calculate_nutritional_value(self, food_dict):

        cur_calories_list = []
        cur_proteins_list = []
        cur_fats_list = []
        cur_carbo_list = []
        cur_price_list = []

        for i_day in range(len(self.min_dict_list)):

            cur_calories_list.append(0)
            cur_proteins_list.append(0)
            cur_fats_list.append(0)
            cur_carbo_list.append(0)
            cur_price_list.append(0)

            min_dict = self.min_dict_list[i_day]

            for key in min_dict:
                cur_quantity = min_dict[key]

                cur_calories_list[-1] += food_dict[key]["calories"] * cur_quantity
                cur_proteins_list[-1] += food_dict[key]["proteins"] * cur_quantity
                cur_fats_list[-1] += food_dict[key]["fats"] * cur_quantity
                cur_carbo_list[-1] += food_dict[key]["carbo"] * cur_quantity

                cur_price_list[-1] += food_dict[key]["price"] * cur_quantity

        return (
            cur_calories_list,
            cur_proteins_list,
            cur_fats_list,
            cur_carbo_list,
            cur_price_list
        )

    def __print_optimal_set_info(
        self,
        start_day,
        food_df,
    ):

        food_dict = food_df.to_dict('index')

        (
            cur_calories_list,
            cur_proteins_list,
            cur_fats_list,
            cur_carbo_list,
            cur_price_list
        ) = self.__calculate_nutritional_value(food_dict)

        for i_day in range(len(cur_price_list)):

            cur_calories = cur_calories_list[i_day]
            cur_proteins = cur_proteins_list[i_day]
            cur_fats = cur_fats_list[i_day]
            cur_carbo = cur_carbo_list[i_day]

            cur_price = cur_price_list[i_day]

            print_list = [
                f"Day {start_day + i_day + 1}:\n"
                f" - calories = {cur_calories:.2f} kcal\n"
                f" - proteins = {cur_proteins:.2f} grams\n"
                f" - fats = {cur_fats:.2f} grams\n"
                f" - carbohydrates = {cur_carbo:.2f} grams\n"
                f" - price = {int(cur_price)} rubles",
            ]

            min_dict = self.min_dict_list[i_day]

            for (i_dish, dish) in enumerate(list(min_dict.keys())):
                dish_dict = food_dict[dish]

                cur_calories = dish_dict["calories"]
                cur_proteins = dish_dict["proteins"]
                cur_fats = dish_dict["fats"]
                cur_carbo = dish_dict["carbo"]

                cur_quantity = min_dict[dish]
                cur_price = dish_dict["price"]
                cur_mass = dish_dict["mass"]

                print_list.append(
                    f"{i_dish + 1}. {dish}" + (f" (x{cur_quantity}):" if cur_quantity > 1 else ":") + "\n"
                    f" - calories = {cur_calories:.2f} kcal\n"
                    f" - proteins = {cur_proteins:.2f} grams\n"
                    f" - fats = {cur_fats:.2f} grams\n"
                    f" - carbohydrates = {cur_carbo:.2f} grams\n"
                    f" - mass = {int(cur_mass)} grams\n"
                    f" - price = {int(cur_price)} rubles"
                )

            self.telegram_handler.log_info("\n\n".join(print_list))

        return food_dict

def get_input_option(
    telegram_handler,
    option_name,
    option_list
):

    def select_from_options():

        option_str = f"Select {option_name}:\n\n" + "\n".join(
            [f"{i}. {option_list[i]}" for i in range(len(option_list))]
        )

        while True:

            try:

                cur_answer = telegram_handler.ask_for_input(option_str)

                input_index = int(cur_answer)

                return option_list[input_index], input_index

            except ValueError:
                continue

            except IndexError:
                continue

    if len(option_list) == 1:

        only_option = option_list[0]
        telegram_handler.log_info(f"You have the only option for {option_name}: {only_option}")

        return only_option, 0

    return select_from_options()

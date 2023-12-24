# food-bot
Optimal VkusVill Dish Recommentation Bot.

This project consists of the following parts:

1. Parser (to parse the current state of dishes)
2. Price optimizer (to find optimal food set in terms of price with some restrictions on calories)
3. Cart loader (to add dishes from the optimal set to my cart)

The full pipeline consists of the following steps (after /start command):

1. Asking me about address, account phone number, pipeline params (the rest are stored in 'config' directory)
2. Opening Google Chrome in so-called headless mode (because GitHub servers do not have displays)
3. Logging into my account (VkusVill sends a code, which I send to telegram bot) - it can be here or after optimization
4. Setting up my address and delivery period (which I also choose via telegram)
5. Parsing the current availability and prices of dishes (npq mode, name-price-quantity) or the full information (including calories, mass, proteins etc.) and storing in the MongoDB
6. Optimizing the price of the daily food set from a subset of 20 dishes selected randomly from the full set (to ensure different results for different days)
7. Checking that I like the sets (and if not, reoptimize with different subset)
8. Adding the dishes to my cart

After that I simply go to my VkusVill cart (via their app) and make the order (I didn't add this step to the algorithm, since it is too risky).

Installation of the project:
1. Install ```docker-compose```
2. Run ```docker-compose up --build``` from repository folder
3. After executing the previous command you can write /start to @vkusvill_food_bot

File description:
1. ```code``` directory consists of python files:
   - ```bot_starter.py``` launches the infinity polling thread, it listens to different users simultaneously
   - ```mongo_connector.py``` connects to the MongoDM base, which saves user data (unique user is unique telegram user token)
   - ```optimizer.py``` optimizes daily set of dishes from VkusVill with respect to price with restrictions on calories, proteins, fats and carbohydrates (parameters, defined by user)
   - ```parser.py``` parses all information from VkusVill as well as loads the dishes to the cart
   - ```pipeline.py``` consists of almost all steps of the bot algorithm to handle user request (others are handles in ```bot_starter.py```)
   - ```telegram_handler.py``` is a file with all methods of sending and receiving messages by bot
   - ```utils.py``` consists of one function needed for choosing between many options via telegram
   
   Note that there are some flags used only for debugging: ```use_telegram```, ```use_mongo```, ```headless```.

2. ```config``` directory consists of one config which was used before MongoDB became supported. It is convenient to look at it and understand how it is stored in MongoDB (the only difference is that chat ids are keys in file and values under key "_id" in MongoDB)
3. ```data``` directory consists of an Excel file of all VkusVill dishes with their nutritional features. It can be updated by choosing ```full``` parsing regime by any user, but it would take at lest 20 minutes to go through it. Data is tabular, and there was no sense to put it into MongoDB, but it would be beneficial to put it into any SQL database
4. ```output``` directory consists of parser outputs for each user (we distinguish between them since they have different addresses, and quantity of dishes is different for them).  The same as for data - these outputs are tabular, and it would be convenient to store them in SQL db. 
5. ```.gitignore``` is a filter for git not to commit some files
6. ```compose.yaml``` is an instruction for ```docker-compose``` what to do
7. ```conda_env.yml``` is an old environment which was conda environment (I switched to poetry, but left this file here just in case)
8. ```Dockerfile``` is an instruction how to set up docker image
9. ```LICENSE``` is just a random license from defaults on GitHub
10. ```poetry.lock``` and ```pyproject.toml``` are environment files for poetry
11. ```README.md``` is this file

I strove to use obvious variable names, so commentary was not so necessary, and I added only a few in complex places. And I also almost never used docstrings, because the functions and methods are somewhat one-timers, and I wouldn't use them for something else. I did not also use defaults parameter values often, because they frequently mixed me up.
Note that all requirements from the task are completed including those which are "beneficial".

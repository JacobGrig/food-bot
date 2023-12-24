import json

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

URI = "mongodb://mongodb:27017/"


class MongoConnector:

    DB_NAME = "vkusvill_bot"
    USERS_COLL_NAME = "users"

    def __init__(self, uri=URI):

        self.client = MongoClient(uri, server_api=ServerApi('1'))

        self.db = self.client[self.DB_NAME]
        self.users_coll = self.db[self.USERS_COLL_NAME]

    def get_config(self, user_id):

        user_filter = {"_id": user_id}

        for value in self.users_coll.find(user_filter):
            return value

        return None

    def set_config(self, config, user_id):

        user_filter = {"_id": user_id}

        config["_id"] = user_id

        self.users_coll.update_one(user_filter, {"$set": config}, upsert=True)

    def update_collection(self, filename):

        config = json.load(filename.open(encoding="utf-8"))

        config_list = []

        for cur_user_id, cur_config in config.items():

            cur_config.update({"_id": int(cur_user_id)})

            config_list.append(cur_config)

        self.users_coll.insert_many(config_list)

    def save_to_file(self, filename):

        config_list = self.users_coll.find()

        config_dict = {}

        for config in config_list:

            user_id = config["_id"]

            del config["_id"]

            config_dict[str(user_id)] = config

        json.dump(config_dict, filename.open('w', encoding='utf-8'), indent=4, ensure_ascii=False)


if __name__ == "__main__":

    # auxiliary script to move old config to MongoDB

    from pathlib import Path

    global_filename = Path(Path(__file__).parent, "..", "config", "config.json")

    mongo_connector = MongoConnector()

    mongo_connector.update_collection(global_filename)
    mongo_connector.save_to_file(global_filename)

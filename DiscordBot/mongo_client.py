from pymongo import MongoClient
import json
import os

# MONGO_PW = os.getenv("MONGO_PASS")
MONGO_HOST = "localhost"
MONGO_PORT = 27017

def insert_record(connection_name: str, document):
    # connection_string = f"mongo"
    client = MongoClient(MONGO_HOST, MONGO_PORT)
    db = client.discord_db
    collection = db[connection_name]

    collection.insert_one(document)
from pymongo import MongoClient
import json
import os

# TODO: set up external database connection
# (will probably need to stand up a Mongo instance on our GCP VM)

MONGO_USER = "cs152-db-user"
MONGO_PW = os.getenv("MONGO_PASS")
MONGO_HOST = "34.168.145.109"
MONGO_PORT = 27017

def insert_record(connection_name: str, document):
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PW)    
    db = client.discord_db
    collection = db[connection_name]

    collection.insert_one(document)

def find_bad_faith_reports(reporter_id: str):
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PW)    
    db = client.discord_db
    collection = db["bad_faith_reports"]
    bad_faith_reports = collection.find({
        "incident_reporter_id": reporter_id,
        "bad_faith_report": True
    })

    return len(list(bad_faith_reports))
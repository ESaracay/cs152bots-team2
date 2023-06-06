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

def find_bad_faith_reports(reporter_id: str):
    client = MongoClient(MONGO_HOST, MONGO_PORT)
    db = client.discord_db
    collection = db["bad_faith_reports"]
    bad_faith_reports = collection.find({
        "incident_reporter_id": reporter_id,
        "bad_faith_report": True
    })

    return len(list(bad_faith_reports))
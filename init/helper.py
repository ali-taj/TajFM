import requests
import pymongo

mongo_url = "mongodb://localhost:27017/"
my_client = pymongo.MongoClient(mongo_url)
database = my_client["Taj"]

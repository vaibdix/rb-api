from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

uri = os.getenv('MONGODB_URL', 'MONGODB_URL_url_not_set')
try:
    client = MongoClient(uri, server_api=ServerApi('1'), tlsAllowInvalidCertificates=True)
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

db = client.todo_db
collection = db["todo_data"]
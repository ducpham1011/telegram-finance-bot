import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import logging

# Load env variables if present
load_dotenv('config.env')

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.uri = os.environ.get("MONGODB_URI")
        self.db_name = os.environ.get("MONGODB_DB_NAME")
        self.client = None
        self.db = None
        
        if not self.uri or not self.db_name:
            logger.warning("MONGODB_URI or MONGODB_DB_NAME not found. Database features will be disabled.")
            return
            
        try:
            self.client = MongoClient(self.uri)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            logger.info("Successfully connected to MongoDB.")
        except ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            self.client = None
            self.db = None

    def get_collection(self, collection_name: str):
        if self.db is not None:
            return self.db[collection_name]
        return None

# Singleton instance
db_manager = DatabaseManager()

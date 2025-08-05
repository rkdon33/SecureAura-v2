import os
import pymongo
from pymongo import MongoClient
from datetime import datetime
import json

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        try:
            # Replace with your actual MongoDB URI
            mongo_uri = "mongodb+srv://rkdon:R4JK4ND3L@secureaura.7ihzga7.mongodb.net/?retryWrites=true&w=majority&appName=SecureAura"

            self.client = MongoClient(mongo_uri)
            self.db = self.client[os.environ.get('MONGODB_DATABASE', 'secureaura')]

            # Test connection
            self.client.admin.command('ping')
            print("Connected to MongoDB successfully")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    def get_collection(self, collection_name):
        return self.db[collection_name]

    # Whitelists methods
    def get_whitelist(self, guild_id):
        collection = self.get_collection('whitelists')
        doc = collection.find_one({"guild_id": str(guild_id)})
        return doc['users'] if doc else []

    def save_whitelist(self, guild_id, users):
        collection = self.get_collection('whitelists')
        collection.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"users": users, "updated_at": datetime.utcnow()}},
            upsert=True
        )

    # Premium servers methods
    def get_premium_server(self, guild_id):
        collection = self.get_collection('premium_servers')
        return collection.find_one({"guild_id": str(guild_id)})

    def save_premium_server(self, guild_id, data):
        collection = self.get_collection('premium_servers')
        data['guild_id'] = str(guild_id)
        data['updated_at'] = datetime.utcnow()
        collection.update_one(
            {"guild_id": str(guild_id)},
            {"$set": data},
            upsert=True
        )

    def get_all_premium_servers(self):
        collection = self.get_collection('premium_servers')
        return {doc['guild_id']: doc for doc in collection.find()}

    # Log channels methods
    def get_log_channel(self, guild_id):
        collection = self.get_collection('log_channels')
        doc = collection.find_one({"guild_id": str(guild_id)})
        return doc['channel_id'] if doc else None

    def save_log_channel(self, guild_id, channel_id):
        collection = self.get_collection('log_channels')
        collection.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"channel_id": channel_id, "updated_at": datetime.utcnow()}},
            upsert=True
        )

    def get_all_log_channels(self):
        """Get all log channels from database"""
        collection = self.get_collection('log_channels')
        return list(collection.find({}, {"_id": 0}))

    def set_greet_settings(self, guild_id, greet_data):
        """Set greet settings for a guild"""
        collection = self.get_collection('greet_settings')
        collection.update_one(
            {"guild_id": guild_id},
            {"$set": greet_data},
            upsert=True
        )

    def get_greet_settings(self, guild_id):
        """Get greet settings for a guild"""
        try:
            result = self.db.greet_settings.find_one({"guild_id": guild_id})
            return result["settings"] if result else None
        except Exception as e:
            print(f"Error getting greet settings: {e}")
            return None

    def set_greet_settings(self, guild_id, settings):
        """Set greet settings for a guild"""
        try:
            self.db.greet_settings.update_one(
                {"guild_id": guild_id},
                {"$set": {"settings": settings}},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error setting greet settings: {e}")
            return False

    def remove_greet_settings(self, guild_id):
        """Remove greet settings for a guild"""
        try:
            self.db.greet_settings.delete_one({"guild_id": guild_id})
            return True
        except Exception as e:
            print(f"Error removing greet settings: {e}")
            return False

    def get_all_greet_settings(self):
        collection = self.get_collection('greet_settings')
        return {doc['guild_id']: doc for doc in collection.find()}

# Global database instance
db = Database()
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def get_mongo_client(uri):
    """
    Create a MongoDB client.
    
    Args:
        uri (str): The MongoDB connection string.
        
    Returns:
        MongoClient: A MongoDB client instance.
    """
    try:
        client = MongoClient(uri)
        # Test the connection
        client.admin.command('ping')
        print("MongoDB connection successful.")
        return client
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
        return None

def get_collection(client, db_name, collection_name):
    """
    Get a collection from the MongoDB database.
    Args:
        client (MongoClient): The MongoDB client instance.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
    Returns:
        Collection: A MongoDB collection instance.
    """
    if client is None:
        print("Client is not connected to MongoDB.")
        return None
    try:
        db = client[db_name]
        collection = db[collection_name]
        return collection
    except Exception as e:
        print(f"Error getting collection: {e}")
        return None
import os
import pandas as pd
from db.mongo_client import get_mongo_client, get_collection
from dotenv import load_dotenv

def load_to_mongodb(df: pd.DataFrame, db_name:str, collection_name:str):
    """
    Load a DataFrame to MongoDB.
    
    Args:
        df (pd.DataFrame): The DataFrame to load.
        db_name (str): The name of the database.
        collection_name (str): The name of the collection.
    """
    # Load environment variables
    load_dotenv()
    
    # Get MongoDB connection string from environment variable
    mongo_uri = os.getenv('MONGO_URI')
    
    # Create a MongoDB client
    client = get_mongo_client(mongo_uri)
    
    # Get the collection
    collection = get_collection(client, db_name, collection_name)
    
    if collection is not None:
        # Convert DataFrame to dictionary format
        data_dict = df.to_dict(orient= "records")
        
        try:
            # Insert data into the collection
            result = collection.insert_many(data_dict)
            print(f"Inserted {len(result.inserted_ids)} records into {db_name}.{collection_name}.")
        except Exception as e:
            print(f"Error inserting data: {e}")
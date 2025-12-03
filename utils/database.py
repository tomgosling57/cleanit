import os
from config import Config
from database import init_db, insert_dummy_data


def populate_database(database_uri: str):
    """This function populates the database with dummy data for testing purposes.
    
    Args:
        database_uri (str): The database URI where the dummy data will be inserted.
    """
    
    if "sqlite:///" in database_uri:
        database_path = database_uri.replace("sqlite:///", "")
        database_dir = os.path.dirname(database_path)
        if not os.path.exists(database_dir):
            os.makedirs(database_dir)

    Session = init_db(database_uri)
    insert_dummy_data(Session)
    print("Database populated with dummy data.")
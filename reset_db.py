import os
from models import init_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def reset_database():
    """Reset the database by removing it and recreating with new schema"""
    try:
        # Remove existing database
        if os.path.exists('faculty_ratings.db'):
            os.remove('faculty_ratings.db')
            print("Removed existing database")
            
        # Initialize new database with updated schema
        engine = create_engine('sqlite:///faculty_ratings.db')
        init_db()
        print("Created new database with updated schema")
        
        return True
    except Exception as e:
        print(f"Error resetting database: {str(e)}")
        return False

if __name__ == "__main__":
    reset_database() 
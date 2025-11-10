import os
import sqlite3
from app import create_app, db

def reset_database():
    """Completely reset the database"""
    app = create_app()
    
    with app.app_context():
        # Get database path from config
        database_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if database_uri.startswith('sqlite:///'):
            db_path = database_uri.replace('sqlite:///', '')
            print(f"Database path: {db_path}")
            
            # Close any existing connections
            db.session.close()
            
            # Delete the database file if it exists
            if os.path.exists(db_path):
                os.remove(db_path)
                print("✅ Old database deleted")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Create new database file
            open(db_path, 'a').close()
            print("✅ New database file created")
            
            # Create all tables
            db.create_all()
            print("✅ All tables created successfully!")
            
            # Verify tables were created
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print("📊 Tables in database:")
            for table in tables:
                print(f"   - {table[0]}")
            conn.close()
        else:
            print("❌ Not using SQLite database")

if __name__ == '__main__':
    reset_database()
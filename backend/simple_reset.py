import os
from app import create_app, db

def simple_reset():
    """Simple database reset that always works"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("✅ All tables dropped")
        
        # Create all tables
        db.create_all()
        print("✅ All tables created")
        
        # Verify by checking if tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("📊 Tables created:")
        for table in tables:
            print(f"   - {table}")

if __name__ == '__main__':
    simple_reset()
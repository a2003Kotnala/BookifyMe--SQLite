from app import create_app, db
from app.models.user import User
from app.models.book import Book
from app.models.bookshelf import Bookshelf
from app.models.group import ReadingGroup, GroupMember

def create_tables():
    """Create all database tables"""
    app = create_app()
    with app.app_context():
        # Drop all tables first (only for development)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("✅ Database tables created successfully!")
        print("📊 Tables created:")
        print("   - users")
        print("   - books") 
        print("   - bookshelves")
        print("   - reading_groups")
        print("   - group_members")

if __name__ == '__main__':
    create_tables()
from app import create_app, db
from app.models.user import User
from sqlalchemy import text

def test_database():
    """Test if database works by creating a test user"""
    app = create_app()
    
    with app.app_context():
        try:
            # Test connection with proper text() wrapper
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful")
            
            # Test User model
            test_user = User(
                name="Test User",
                email="test@example.com"
            )
            test_user.set_password("Test1234")
            
            db.session.add(test_user)
            db.session.commit()
            print("✅ User creation successful")
            
            # Test query
            user = User.query.filter_by(email="test@example.com").first()
            if user and user.check_password("Test1234"):
                print("✅ User login test successful")
            else:
                print("❌ User login test failed")
                
            # Clean up
            db.session.delete(user)
            db.session.commit()
            print("✅ Test cleanup successful")
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")

if __name__ == '__main__':
    test_database()
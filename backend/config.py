import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    
    # Database configuration - SQLite as default
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite://instance/bookifyme.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # Google Books API
    GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY') or 'your-google-books-api-key'
    GOOGLE_BOOKS_BASE_URL = 'https://www.googleapis.com/books/v1/volumes'
    
    # CORS
    FRONTEND_URL = os.environ.get('FRONTEND_URL') or 'http://localhost:3000'
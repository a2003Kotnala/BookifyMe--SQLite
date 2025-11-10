from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException

from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
cors = CORS()

def create_app(config_class=Config):
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    
    # CORS configuration - allow all origins for development
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500", 
                "http://127.0.0.1:5000",
                "http://localhost:5000"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize services
    from app.services.google_books import google_books_service
    google_books_service.init_app(app)
    
    # Initialize email service
    from app.services.email_service import email_service
    email_service.init_app(app)
    
    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.bookshelf import bookshelf_bp
    from app.routes.community import community_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(books_bp, url_prefix='/api/books')
    app.register_blueprint(bookshelf_bp, url_prefix='/api/bookshelf')
    app.register_blueprint(community_bp, url_prefix='/api/community')
    
    # Register API Routes
    @app.route('/')
    def hello():
        return jsonify({
            "message": "📚 Welcome to BookifyMe API!",
            "version": "1.0",
            "status": "Server is running 🚀",
            "database": app.config['SQLALCHEMY_DATABASE_URI']
        })
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy"})

    # Custom JSON Error Handling
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        return jsonify({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }), e.code

    @app.errorhandler(500)
    def handle_500_error(e):
        return jsonify({
            "code": 500,
            "name": "Internal Server Error",
            "description": "An internal server error occurred"
        }), 500

    # Shell context for Flask CLI
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Book 
        return {'db': db, 'User': User, 'Book': Book}

    return app
# app/__init__.py

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException # Import for handling HTTP errors

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
    # Your specific origin setup is good practice for security!
    cors.init_app(app, origins=[app.config.get('FRONTEND_URL', 'http://localhost:3000')])
    
    # Initialize services
    from app.services.google_books import google_books_service
    google_books_service.init_app(app)
    
    # --- Register Blueprints ---
    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.bookshelf import bookshelf_bp
    from app.routes.community import community_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(books_bp, url_prefix='/api/books')
    app.register_blueprint(bookshelf_bp, url_prefix='/api/bookshelf')
    app.register_blueprint(community_bp, url_prefix='/api/community')
    
    # --- Register API Routes ---
    @app.route('/')
    def hello():
        return jsonify({
            "message": "📚 Welcome to BookifyMe API!",
            "version": "1.0",
            "status": "Server is running 🚀"
        })
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy"})

    # --- Add custom JSON Error Handling ---
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        response = e.get_response()
        response.data = jsonify({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }).data
        response.content_type = "application/json"
        return response

    # --- Add a developer-friendly shell context ---
    # This makes 'db' and your models automatically available in `flask shell`
    @app.shell_context_processor
    def make_shell_context():
        # Make sure to import your models here
        from app.models import User, Book 
        return {'db': db, 'User': User, 'Book': Book}

    return app
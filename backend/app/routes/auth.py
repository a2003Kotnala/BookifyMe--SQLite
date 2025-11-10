from flask import Blueprint, request
from app import db
from app.models.user import User
from app.utils.helpers import api_response, validate_email, validate_password
from app.utils.auth import jwt_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('email') or not data.get('password') or not data.get('name'):
            return api_response(None, 'Name, email and password are required', 400)
        
        name = data.get('name').strip()
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        # Validate email format
        if not validate_email(email):
            return api_response(None, 'Invalid email format', 400)
        
        # Validate password strength
        is_valid_password, password_msg = validate_password(password)
        if not is_valid_password:
            return api_response(None, password_msg, 400)
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return api_response(None, 'User with this email already exists', 409)
        
        # Create new user
        user = User(name=name, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate auth token
        token = user.generate_auth_token()
        
        return api_response({
            'user': user.to_dict(),
            'token': token
        }, 'User registered successfully', 201)
        
    except Exception as e:
        db.session.rollback()
        return api_response(None, 'Registration failed', 500, str(e))

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return api_response(None, 'Email and password are required', 400)
        
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return api_response(None, 'Invalid email or password', 401)
        
        # Generate auth token
        token = user.generate_auth_token()
        
        return api_response({
            'user': user.to_dict(),
            'token': token
        }, 'Login successful')
        
    except Exception as e:
        return api_response(None, 'Login failed', 500, str(e))

@auth_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user(current_user):
    return api_response({
        'user': current_user.to_dict()
    }, 'User data retrieved successfully')

@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout(current_user):
    # With JWT, logout is handled on the client side by removing the token
    return api_response(None, 'Logout successful')
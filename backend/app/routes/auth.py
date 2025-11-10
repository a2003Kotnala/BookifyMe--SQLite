from flask import Blueprint, request, current_app
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.utils.helpers import api_response, validate_email, validate_password
from app.utils.auth import jwt_required
import traceback

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return api_response(None, 'No data provided', 400)
        
        if not data.get('email'):
            return api_response(None, 'Email is required', 400)
        
        if not data.get('password'):
            return api_response(None, 'Password is required', 400)
        
        if not data.get('name'):
            return api_response(None, 'Name is required', 400)
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validate email format
        if not validate_email(email):
            return api_response(None, 'Invalid email format', 400)
        
        # Validate password strength
        is_valid_password, password_msg = validate_password(password)
        if not is_valid_password:
            return api_response(None, password_msg, 400)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
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
        current_app.logger.error(f"Registration error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return api_response(None, 'Registration failed: ' + str(e), 500)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return api_response(None, 'No data provided', 400)
        
        if not data.get('email'):
            return api_response(None, 'Email is required', 400)
        
        if not data.get('password'):
            return api_response(None, 'Password is required', 400)
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return api_response(None, 'Invalid email or password', 401)
        
        if not user.check_password(password):
            return api_response(None, 'Invalid email or password', 401)
        
        # Generate auth token
        token = user.generate_auth_token()
        
        return api_response({
            'user': user.to_dict(),
            'token': token
        }, 'Login successful')
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return api_response(None, 'Login failed: ' + str(e), 500)

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return api_response(None, 'Email is required', 400)
        
        email = data.get('email').strip().lower()
        user = User.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        if not user:
            return api_response(None, 'If the email exists, a password reset link has been sent.', 200)
        
        # Generate reset token
        reset_token = user.generate_reset_token()
        db.session.commit()
        
        # Import email service here to avoid circular imports
        from app.services.email_service import email_service
        email_service.send_password_reset_email(user.email, reset_token)
        
        return api_response(None, 'If the email exists, a password reset link has been sent.', 200)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Forgot password error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return api_response(None, 'Failed to process reset request: ' + str(e), 500)

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        
        if not data or not data.get('token') or not data.get('new_password'):
            return api_response(None, 'Token and new password are required', 400)
        
        token = data.get('token')
        new_password = data.get('new_password')
        
        # Validate password strength
        is_valid_password, password_msg = validate_password(new_password)
        if not is_valid_password:
            return api_response(None, password_msg, 400)
        
        user = User.query.filter_by(reset_token=token).first()
        
        if not user or not user.verify_reset_token(token):
            return api_response(None, 'Invalid or expired reset token', 400)
        
        # Update password
        user.set_password(new_password)
        user.clear_reset_token()
        db.session.commit()
        
        return api_response(None, 'Password reset successfully')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Reset password error: {str(e)}")
        return api_response(None, 'Failed to reset password: ' + str(e), 500)

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
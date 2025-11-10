import re
from flask import jsonify

def validate_email(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
        
    # More permissive email validation for testing
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, "Password is valid"

def api_response(data=None, message="", status=200, error=None):
    """Standard API response format"""
    response = {
        'success': status < 400,
        'message': message,
        'data': data
    }
    
    if error:
        response['error'] = error
    
    return jsonify(response), status

def paginate_query(query, page=1, per_page=20):
    """Paginate SQLAlchemy query"""
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }
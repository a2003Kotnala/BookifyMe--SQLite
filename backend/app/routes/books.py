from flask import Blueprint, request
from app.services.google_books import GoogleBooksService
from app.utils.helpers import api_response
from app.utils.auth import jwt_required

books_bp = Blueprint('books', __name__)
google_books_service = GoogleBooksService()

@books_bp.route('/search', methods=['GET'])
def search_books():
    try:
        query = request.args.get('q', '')
        max_results = int(request.args.get('limit', 12))
        start_index = int(request.args.get('offset', 0))
        
        if not query:
            return api_response(None, 'Search query is required', 400)
        
        books, total_count = google_books_service.search_books(
            query, max_results, start_index
        )
        
        return api_response({
            'books': books,
            'total_count': total_count,
            'query': query
        }, 'Books search successful')
        
    except Exception as e:
        return api_response(None, 'Search failed', 500, str(e))

@books_bp.route('/categories/<category>', methods=['GET'])
def get_books_by_category(category):
    try:
        max_results = int(request.args.get('limit', 12))
        
        books, total_count = google_books_service.get_books_by_category(
            category, max_results
        )
        
        return api_response({
            'books': books,
            'total_count': total_count,
            'category': category
        }, f'Books in {category} category')
        
    except Exception as e:
        return api_response(None, 'Failed to fetch category books', 500, str(e))

@books_bp.route('/<book_id>', methods=['GET'])
def get_book_details(book_id):
    try:
        book = google_books_service.get_book_by_id(book_id)
        
        if not book:
            return api_response(None, 'Book not found', 404)
        
        return api_response({
            'book': book
        }, 'Book details retrieved successfully')
        
    except Exception as e:
        return api_response(None, 'Failed to fetch book details', 500, str(e))

@books_bp.route('/bestsellers', methods=['GET'])
def get_bestsellers():
    try:
        # Get popular books from various categories
        categories = ['fiction', 'science', 'technology', 'history', 'biography']
        all_books = []
        
        for category in categories[:3]:  # Limit to 3 categories for performance
            books, _ = google_books_service.get_books_by_category(category, 4)
            all_books.extend(books)
        
        # Sort by rating
        all_books.sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        return api_response({
            'books': all_books[:12]  # Return top 12
        }, 'Bestsellers retrieved successfully')
        
    except Exception as e:
        return api_response(None, 'Failed to fetch bestsellers', 500, str(e))
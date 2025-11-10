import logging
import json
from flask import Blueprint, request
from app import db
from app.models.bookshelf import Bookshelf
from app.models.book import Book
from app.services.google_books import GoogleBooksService
from app.utils.helpers import api_response
from app.utils.auth import jwt_required

bookshelf_bp = Blueprint('bookshelf', __name__)
google_books_service = GoogleBooksService()

@bookshelf_bp.route('', methods=['GET'])
@jwt_required
def get_bookshelf(current_user):
    """Retrieves all bookshelf entries for the current user, organized by shelf."""
    try:
        bookshelf_entries = Bookshelf.query.filter_by(user_id=current_user.id).all()
        
        organized_shelves = {
            'reading': [],
            'wantToRead': [],
            'finished': []
        }
        
        for entry in bookshelf_entries:
            if entry.shelf_type in organized_shelves:
                book_dict = {
                    'book': {
                        'id': entry.book.google_books_id,
                        'google_books_id': entry.book.google_books_id,
                        'title': entry.book.title,
                        'authors': entry.book.get_authors(),
                        'thumbnail': entry.book.thumbnail,
                        'page_count': entry.book.page_count,
                        'description': entry.book.description,
                        'average_rating': entry.book.average_rating,
                        'preview_link': entry.book.preview_link,
                        'info_link': entry.book.info_link,
                        'volumeInfo': {
                            'title': entry.book.title,
                            'authors': entry.book.get_authors(),
                            'imageLinks': {
                                'thumbnail': entry.book.thumbnail
                            } if entry.book.thumbnail else {},
                            'pageCount': entry.book.page_count,
                            'description': entry.book.description,
                            'averageRating': entry.book.average_rating,
                            'previewLink': entry.book.preview_link,
                            'infoLink': entry.book.info_link
                        }
                    },
                    'shelf_type': entry.shelf_type,
                    'added_at': entry.added_at.isoformat() if entry.added_at else None
                }
                organized_shelves[entry.shelf_type].append(book_dict)
        
        return api_response({'bookshelves': organized_shelves}, 'Bookshelf retrieved successfully')
        
    except Exception as e:
        logging.error(f"Error fetching bookshelf for user {current_user.id}: {e}", exc_info=True)
        return api_response(None, 'Failed to fetch bookshelf', 500)

@bookshelf_bp.route('/add', methods=['POST'])
@jwt_required
def add_to_bookshelf(current_user):
    """
    Adds a new book to a shelf or moves an existing book to a different shelf.
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('book_id') or not data.get('shelf_type'):
            return api_response(None, 'Book ID and shelf type are required', 400)
        
        book_id = data.get('book_id')
        shelf_type = data.get('shelf_type')
        book_data = data.get('book_data', {})
        
        if shelf_type not in ['reading', 'wantToRead', 'finished']:
            return api_response(None, 'Invalid shelf type', 400)
        
        # --- Transaction Start ---
        
        # Step 1: Find the book in our local DB or create it from Google's API or provided book_data.
        book = Book.query.filter_by(google_books_id=book_id).first()
        
        if not book:
            # Use provided book_data if available, otherwise fetch from Google Books API
            if book_data:
                book = Book(
                    google_books_id=book_id,
                    title=book_data.get('title', 'Unknown Title'),
                    description=book_data.get('description', ''),
                    thumbnail=book_data.get('thumbnail', ''),
                    average_rating=book_data.get('average_rating', 0),
                    ratings_count=book_data.get('ratings_count', 0),
                    published_date=book_data.get('published_date', ''),
                    page_count=book_data.get('page_count', 0),
                    language=book_data.get('language', 'en'),
                    preview_link=book_data.get('preview_link', ''),
                    info_link=book_data.get('info_link', '')
                )
                book.set_authors(book_data.get('authors', ['Unknown Author']))
                book.set_categories(book_data.get('categories', []))
            else:
                # Fetch book details from Google Books API
                book_data_from_google = google_books_service.get_book_by_id(book_id)
                if not book_data_from_google:
                    return api_response(None, 'Book not found via Google API', 404)
                
                book = Book(
                    google_books_id=book_id,
                    title=book_data_from_google.get('title', 'Unknown Title'),
                    description=book_data_from_google.get('description', ''),
                    thumbnail=book_data_from_google.get('thumbnail', ''),
                    average_rating=book_data_from_google.get('average_rating', 0),
                    ratings_count=book_data_from_google.get('ratings_count', 0),
                    published_date=book_data_from_google.get('published_date', ''),
                    page_count=book_data_from_google.get('page_count', 0),
                    language=book_data_from_google.get('language', 'en'),
                    preview_link=book_data_from_google.get('preview_link', ''),
                    info_link=book_data_from_google.get('info_link', '')
                )
                book.set_authors(book_data_from_google.get('authors', ['Unknown Author']))
                book.set_categories(book_data_from_google.get('categories', []))
            
            db.session.add(book)
            db.session.flush()

        # Step 2: Check if book already exists in user's bookshelf
        existing_entry = Bookshelf.query.filter_by(
            user_id=current_user.id, 
            book_id=book.id
        ).first()
        
        if existing_entry:
            # Update existing entry
            existing_entry.shelf_type = shelf_type
            message = 'Book moved to new shelf'
        else:
            # Create new entry
            new_entry = Bookshelf(
                user_id=current_user.id,
                book_id=book.id,
                shelf_type=shelf_type
            )
            db.session.add(new_entry)
            message = 'Book added to shelf'
        
        db.session.commit()
        
        return api_response(None, message)
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to add book for user {current_user.id}: {e}", exc_info=True)
        return api_response(None, 'An error occurred while updating your shelf', 500)

@bookshelf_bp.route('/move', methods=['POST'])
@jwt_required
def move_book(current_user):
    """Moves a book already on a user's shelf to a new shelf."""
    try:
        data = request.get_json()
        
        if not data or not data.get('book_id') or not data.get('to_shelf'):
            return api_response(None, 'Book ID and to_shelf are required', 400)
        
        google_book_id = data.get('book_id')
        to_shelf = data.get('to_shelf')
        
        if to_shelf not in ['reading', 'wantToRead', 'finished']:
            return api_response(None, 'Invalid shelf type', 400)
        
        # Find the bookshelf entry
        entry = db.session.query(Bookshelf).join(Book).filter(
            Bookshelf.user_id == current_user.id,
            Book.google_books_id == google_book_id
        ).first()
        
        if not entry:
            return api_response(None, 'Book not found in your bookshelf', 404)
        
        entry.shelf_type = to_shelf
        db.session.commit()
        
        return api_response(None, 'Book moved successfully')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to move book for user {current_user.id}: {e}", exc_info=True)
        return api_response(None, 'Failed to move book', 500)

@bookshelf_bp.route('/remove', methods=['POST'])
@jwt_required
def remove_from_bookshelf(current_user):
    """Removes a book from the user's bookshelf."""
    try:
        data = request.get_json()
        if not data or not data.get('book_id'):
            return api_response(None, 'Book ID is required', 400)
        
        google_book_id = data.get('book_id')
        shelf_type = data.get('shelf_type')  # Optional, for validation
        
        # Find the bookshelf entry
        entry = db.session.query(Bookshelf).join(Book).filter(
            Bookshelf.user_id == current_user.id,
            Book.google_books_id == google_book_id
        ).first()
        
        if not entry:
            return api_response(None, 'Book not found in your bookshelf', 404)
        
        # Optional: validate shelf type if provided
        if shelf_type and entry.shelf_type != shelf_type:
            return api_response(None, 'Book not found in specified shelf', 404)
        
        db.session.delete(entry)
        db.session.commit()
        
        return api_response(None, 'Book removed from shelf')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to remove book for user {current_user.id}: {e}", exc_info=True)
        return api_response(None, 'Failed to remove book', 500)

@bookshelf_bp.route('/stats', methods=['GET'])
@jwt_required
def get_reading_stats(current_user):
    """Retrieves reading statistics for the current user."""
    try:
        # Get counts for each shelf type
        reading_count = Bookshelf.query.filter_by(
            user_id=current_user.id, 
            shelf_type='reading'
        ).count()
        
        want_to_read_count = Bookshelf.query.filter_by(
            user_id=current_user.id, 
            shelf_type='wantToRead'
        ).count()
        
        finished_count = Bookshelf.query.filter_by(
            user_id=current_user.id, 
            shelf_type='finished'
        ).count()
        
        # Calculate total pages read from finished books
        finished_books = db.session.query(Book).join(Bookshelf).filter(
            Bookshelf.user_id == current_user.id,
            Bookshelf.shelf_type == 'finished'
        ).all()
        
        total_pages = sum(book.page_count or 0 for book in finished_books)
        
        # Get unique genres (simplified - count unique categories)
        all_books = db.session.query(Book).join(Bookshelf).filter(
            Bookshelf.user_id == current_user.id
        ).all()
        
        unique_categories = set()
        for book in all_books:
            categories = book.get_categories()
            if categories:
                unique_categories.update(categories)
        
        stats = {
            'total_books_read': finished_count,
            'total_pages_read': total_pages,
            'unique_genres': len(unique_categories),
            'currently_reading': reading_count,
            'want_to_read': want_to_read_count
        }
        
        return api_response({'stats': stats}, 'Reading statistics retrieved successfully')
        
    except Exception as e:
        logging.error(f"Failed to fetch stats for user {current_user.id}: {e}", exc_info=True)
        return api_response(None, 'Failed to fetch reading statistics', 500)
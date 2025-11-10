import logging
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
                # Assuming entry.to_dict() correctly serializes the book data
                organized_shelves[entry.shelf_type].append(entry.to_dict())
        
        return api_response({'bookshelves': organized_shelves}, 'Bookshelf retrieved successfully')
        
    except Exception as e:
        logging.error(f"Error fetching bookshelf for user {current_user.id}: {e}", exc_info=True)
        return api_response(None, 'Failed to fetch bookshelf', 500)

@bookshelf_bp.route('/add', methods=['POST'])
@jwt_required
def add_to_bookshelf(current_user):
    """
    Adds a new book to a shelf or moves an existing book to a different shelf.
    This is now a single, robust database transaction.
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('book_id') or not data.get('shelf_type'):
            return api_response(None, 'Book ID and shelf type are required', 400)
        
        book_id = data.get('book_id')
        shelf_type = data.get('shelf_type')
        
        if shelf_type not in ['reading', 'wantToRead', 'finished']:
            return api_response(None, 'Invalid shelf type', 400)
        
        # --- Transaction Start ---
        
        # Step 1: Find the book in our local DB or create it from Google's API.
        book = Book.query.filter_by(google_books_id=book_id).first()
        
        if not book:
            # Fetch book details from Google Books API
            book_data = google_books_service.get_book_by_id(book_id)
            if not book_data:
                return api_response(None, 'Book not found via Google API', 404)
            
            # Create a new book object but DON'T commit yet.
            book = Book(
                google_books_id=book_id,
                title=book_data.get('title'),
                description=book_data.get('description'),
                thumbnail=book_data.get('thumbnail'),
                average_rating=book_data.get('rating'),
                ratings_count=book_data.get('ratings_count'),
                published_date=book_data.get('published_date'),
                page_count=book_data.get('page_count'),
                language=book_data.get('language'),
                preview_link=book_data.get('preview_link'),
                info_link=book_data.get('info_link')
            )
            book.set_authors(book_data.get('authors', []))
            book.set_categories(book_data.get('categories', []))
            
            db.session.add(book)
            # Use flush to get the new book's primary key (book.id) without ending the transaction.
            db.session.flush()

        # Step 2: Now, find or update the bookshelf entry for this user and book.
        existing_entry = Bookshelf.query.filter_by(
            user_id=current_user.id, 
            book_id=book.id  # We can use book.id here because of the flush above
        ).first()
        
        if existing_entry:
            # The user already has this book, so just move it.
            existing_entry.shelf_type = shelf_type
            message = 'Book moved to new shelf'
        else:
            # This is a new book for the user's shelf.
            new_entry = Bookshelf(
                user_id=current_user.id,
                book_id=book.id,
                shelf_type=shelf_type
            )
            db.session.add(new_entry)
            message = 'Book added to shelf'
        
        # Step 3: Commit the entire transaction at once.
        # This saves the new book (if any) AND the new/updated shelf entry.
        db.session.commit()
        # --- Transaction End ---
        
        return api_response(None, message)
        
    except Exception as e:
        # If anything fails, roll back all changes to keep the DB consistent.
        db.session.rollback()
        logging.error(f"Failed to add book for user {current_user.id}: {e}", exc_info=True)
        return api_response(None, 'An error occurred while updating your shelf', 500)

@bookshelf_bp.route('/move', methods=['PUT'])
@jwt_required
def move_book(current_user):
    """Moves a book already on a user's shelf to a new shelf."""
    try:
        data = request.get_json()
        
        if not data or not data.get('book_id') or not data.get('new_shelf'):
            return api_response(None, 'Book ID and new shelf are required', 400)
        
        google_book_id = data.get('book_id')
        new_shelf = data.get('new_shelf')
        
        if new_shelf not in ['reading', 'wantToRead', 'finished']:
            return api_response(None, 'Invalid shelf type', 400)
        
        # Find the bookshelf entry directly
        entry = db.session.query(Bookshelf).join(Book).filter(
            Bookshelf.user_id == current_user.id,
            Book.google_books_id == google_book_id
        ).first()
        
        if not entry:
            return api_response(None, 'Book not found in your bookshelf', 404)
        
        entry.shelf_type = new_shelf
        db.session.commit()
        
        return api_response(None, 'Book moved successfully')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to move book for user {current_user.id}: {e}", exc_info=True)
        return api_response(None, 'Failed to move book', 500)

@bookshelf_bp.route('/<google_book_id>', methods=['DELETE'])
@jwt_required
def remove_from_bookshelf(current_user, google_book_id):
    """Removes a book from the user's bookshelf."""
    try:
        entry = db.session.query(Bookshelf).join(Book).filter(
            Bookshelf.user_id == current_user.id,
            Book.google_books_id == google_book_id
        ).first()
        
        if not entry:
            return api_response(None, 'Book not found in your bookshelf', 404)
        
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
        from app.services.statistics import StatisticsService
        stats = StatisticsService.get_user_reading_stats(current_user.id)
        return api_response({'stats': stats}, 'Reading statistics retrieved successfully')
        
    except Exception as e:
        logging.error(f"Failed to fetch stats for user {current_user.id}: {e}", exc_info=True)
        return api_response(None, 'Failed to fetch reading statistics', 500)

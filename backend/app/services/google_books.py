import requests
from flask import current_app
from app.models.book import Book
from app import db

class GoogleBooksService:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.api_key = app.config.get('GOOGLE_BOOKS_API_KEY')
        self.base_url = app.config.get('GOOGLE_BOOKS_BASE_URL', 'https://www.googleapis.com/books/v1/volumes')
    
    def _get_config(self):
        """Get configuration from current_app or stored app"""
        if current_app:
            return current_app.config.get('GOOGLE_BOOKS_API_KEY'), current_app.config.get('GOOGLE_BOOKS_BASE_URL')
        elif self.app:
            return self.app.config.get('GOOGLE_BOOKS_API_KEY'), self.app.config.get('GOOGLE_BOOKS_BASE_URL')
        else:
            return None, 'https://www.googleapis.com/books/v1/volumes'
    
    def search_books(self, query, max_results=12, start_index=0):
        """Search books using Google Books API"""
        try:
            api_key, base_url = self._get_config()
            url = f"{base_url}?q={query}&maxResults={max_results}&startIndex={start_index}"
            if api_key and api_key != 'your-google-books-api-key':
                url += f"&key={api_key}"
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            books = []
            if data.get('items'):
                for item in data['items']:
                    book = self._process_book_item(item)
                    if book:
                        books.append(book)
            
            return books, len(books)
            
        except requests.RequestException as e:
            print(f"Google Books API error: {str(e)}")
            return [], 0
        except Exception as e:
            print(f"Unexpected error in search_books: {str(e)}")
            return [], 0
    
    def get_books_by_category(self, category, max_results=12):
        """Get books by category"""
        query = f"subject:{category}"
        return self.search_books(query, max_results)
    
    def get_book_by_id(self, google_books_id):
        """Get book details by Google Books ID"""
        try:
            api_key, base_url = self._get_config()
            url = f"{base_url}/{google_books_id}"
            if api_key and api_key != 'your-google-books-api-key':
                url += f"?key={api_key}"
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            return self._process_book_item(data)
            
        except requests.RequestException as e:
            print(f"Google Books API error: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error in get_book_by_id: {str(e)}")
            return None
    
    def _process_book_item(self, item):
        """Process Google Books API item and cache in database"""
        if not item.get('id'):
            return None
        
        # Check if book already exists in our database
        existing_book = Book.query.filter_by(google_books_id=item['id']).first()
        if existing_book:
            return existing_book.to_dict()
        
        # Create new book in database
        try:
            book = Book.create_from_google_books(item)
            db.session.add(book)
            db.session.commit()
            return book.to_dict()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving book to database: {str(e)}")
            # Return basic book info even if save fails
            return self._format_book_data(item)
    
    def _format_book_data(self, item):
        """Format book data without saving to database"""
        volume_info = item.get('volumeInfo', {})
        sale_info = item.get('saleInfo', {})
        
        return {
            'id': item.get('id'),
            'google_books_id': item.get('id'),
            'title': volume_info.get('title', 'Unknown Title'),
            'authors': volume_info.get('authors', ['Unknown Author']),
            'description': volume_info.get('description', 'No description available.'),
            'categories': volume_info.get('categories', []),
            'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail') or 
                        volume_info.get('imageLinks', {}).get('smallThumbnail'),
            'rating': volume_info.get('averageRating') or 0,
            'ratings_count': volume_info.get('ratingsCount') or 0,
            'published_date': volume_info.get('publishedDate'),
            'page_count': volume_info.get('pageCount'),
            'language': volume_info.get('language'),
            'preview_link': volume_info.get('previewLink'),
            'info_link': volume_info.get('infoLink'),
            'price': sale_info.get('listPrice', {}).get('amount'),
            'currency': sale_info.get('listPrice', {}).get('currencyCode')
        }

# Create service instance (will be initialized later)
google_books_service = GoogleBooksService()
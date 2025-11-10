from app.models.bookshelf import Bookshelf
from app.models.book import Book
from collections import Counter

class StatisticsService:
    @staticmethod
    def get_user_reading_stats(user_id):
        """Get comprehensive reading statistics for a user"""
        user_bookshelves = Bookshelf.query.filter_by(user_id=user_id).all()
        
        finished_books = [bs for bs in user_bookshelves if bs.shelf_type == 'finished']
        reading_books = [bs for bs in user_bookshelves if bs.shelf_type == 'reading']
        want_to_read_books = [bs for bs in user_bookshelves if bs.shelf_type == 'wantToRead']
        
        # Calculate statistics
        total_books_read = len(finished_books)
        
        total_pages = 0
        genres = set()
        total_rating = 0
        rated_books = 0
        
        for bookshelf in finished_books:
            book = bookshelf.book
            if book:
                if book.page_count:
                    total_pages += book.page_count
                
                if book.categories:
                    categories = book.get_categories()
                    for category in categories:
                        genres.add(category)
                
                if book.average_rating:
                    total_rating += book.average_rating
                    rated_books += 1
        
        avg_rating = total_rating / rated_books if rated_books > 0 else 0
        
        # Get reading progress
        currently_reading_count = len(reading_books)
        wishlist_count = len(want_to_read_books)
        
        # Get genre distribution
        genre_counter = Counter()
        for bookshelf in user_bookshelves:
            book = bookshelf.book
            if book and book.categories:
                categories = book.get_categories()
                for category in categories:
                    genre_counter[category] += 1
        
        top_genres = dict(genre_counter.most_common(5))
        
        return {
            'total_books_read': total_books_read,
            'total_pages_read': total_pages,
            'unique_genres': len(genres),
            'average_rating': round(avg_rating, 1),
            'currently_reading': currently_reading_count,
            'want_to_read': wishlist_count,
            'top_genres': top_genres,
            'reading_progress': {
                'finished': total_books_read,
                'reading': currently_reading_count,
                'want_to_read': wishlist_count
            }
        }
    
    @staticmethod
    def get_reading_timeline(user_id):
        """Get reading activity timeline"""
        # This would track reading activity over time
        # For now, return basic structure
        return {
            'timeline': [],
            'streak': 0,
            'weekly_activity': []
        }
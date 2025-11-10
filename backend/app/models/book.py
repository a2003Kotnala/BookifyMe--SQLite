from app import db
import json

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    google_books_id = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    authors = db.Column(db.Text)  # Store as JSON string
    description = db.Column(db.Text)
    categories = db.Column(db.Text)  # Store as JSON string
    thumbnail = db.Column(db.String(500))
    average_rating = db.Column(db.Float)
    ratings_count = db.Column(db.Integer)
    published_date = db.Column(db.String(50))
    page_count = db.Column(db.Integer)
    language = db.Column(db.String(10))
    preview_link = db.Column(db.String(500))
    info_link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    bookshelf_entries = db.relationship('Bookshelf', backref='book', lazy=True, cascade='all, delete-orphan')
    
    def set_authors(self, authors_list):
        if authors_list:
            self.authors = json.dumps(authors_list)
    
    def get_authors(self):
        if self.authors:
            try:
                return json.loads(self.authors)
            except json.JSONDecodeError:
                return [self.authors]  # Fallback if it's not valid JSON
        return []
    
    def set_categories(self, categories_list):
        if categories_list:
            self.categories = json.dumps(categories_list)
    
    def get_categories(self):
        if self.categories:
            try:
                return json.loads(self.categories)
            except json.JSONDecodeError:
                return [self.categories]  # Fallback if it's not valid JSON
        return []
    
    def to_dict(self):
        return {
            'id': self.id,
            'google_books_id': self.google_books_id,
            'title': self.title,
            'authors': self.get_authors(),
            'description': self.description,
            'categories': self.get_categories(),
            'thumbnail': self.thumbnail,
            'rating': self.average_rating or 0,
            'ratings_count': self.ratings_count or 0,
            'published_date': self.published_date,
            'page_count': self.page_count,
            'language': self.language,
            'preview_link': self.preview_link,
            'info_link': self.info_link
        }
    
    @classmethod
    def create_from_google_books(cls, google_book_data):
        """Create a Book instance from Google Books API data"""
        volume_info = google_book_data.get('volumeInfo', {})
        
        book = cls(
            google_books_id=google_book_data.get('id'),
            title=volume_info.get('title', 'Unknown Title'),
            description=volume_info.get('description', 'No description available.'),
            thumbnail=volume_info.get('imageLinks', {}).get('thumbnail') or 
                     volume_info.get('imageLinks', {}).get('smallThumbnail'),
            average_rating=volume_info.get('averageRating'),
            ratings_count=volume_info.get('ratingsCount'),
            published_date=volume_info.get('publishedDate'),
            page_count=volume_info.get('pageCount'),
            language=volume_info.get('language'),
            preview_link=volume_info.get('previewLink'),
            info_link=volume_info.get('infoLink')
        )
        
        book.set_authors(volume_info.get('authors', ['Unknown Author']))
        book.set_categories(volume_info.get('categories', []))
        
        return book
    
    def __repr__(self):
        return f'<Book {self.title}>'
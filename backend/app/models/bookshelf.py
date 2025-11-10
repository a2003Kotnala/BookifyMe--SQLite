from app import db
from datetime import datetime

class Bookshelf(db.Model):
    __tablename__ = 'bookshelves'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    shelf_type = db.Column(db.Enum('reading', 'wantToRead', 'finished'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_user_book'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'shelf_type': self.shelf_type,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'book': self.book.to_dict() if self.book else None
        }
    
    def __repr__(self):
        return f'<Bookshelf user:{self.user_id} book:{self.book_id} shelf:{self.shelf_type}>'
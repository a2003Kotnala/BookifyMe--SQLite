from app import db
from datetime import datetime

class ReadingGroup(db.Model):
    __tablename__ = 'reading_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)
    
    # Relationships
    members = db.relationship('GroupMember', backref='group', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_public': self.is_public,
            'member_count': len(self.members)
        }
    
    def __repr__(self):
        return f'<ReadingGroup {self.name}>'

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('reading_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.Enum('admin', 'member'), default='member')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='unique_group_member'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'role': self.role,
            'user': self.user.to_dict() if self.user else None
        }
    
    def __repr__(self):
        return f'<GroupMember group:{self.group_id} user:{self.user_id}>'
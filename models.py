from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import datetime

# Database instance will be initialized in app.py
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    favorites = relationship('Favorite', back_populates='user', cascade='all, delete-orphan')
    predictions = relationship('Prediction', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set the user's password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
class Favorite(db.Model):
    """User saved favorites model"""
    __tablename__ = 'favorites'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    prediction_id = Column(String(36), ForeignKey('predictions.id', ondelete='CASCADE'), nullable=False)
    added_at = Column(DateTime, default=func.now())
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='favorites')
    prediction = relationship('Prediction', back_populates='favorites')
    
    def __repr__(self):
        return f'<Favorite {self.id} by User {self.user_id}>'
    
class Prediction(db.Model):
    """Style prediction results model"""
    __tablename__ = 'predictions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    image_path = Column(String(255), nullable=False)
    primary_style = Column(String(100), nullable=False)
    style_tags = Column(Text, nullable=True)  # Stored as JSON string
    confidence_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship('User', back_populates='predictions')
    favorites = relationship('Favorite', back_populates='prediction', cascade='all, delete-orphan')
    feedback = relationship('Feedback', back_populates='prediction', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Prediction {self.id} - {self.primary_style}>'
        
class Feedback(db.Model):
    """User feedback on prediction accuracy"""
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    prediction_id = Column(String(36), ForeignKey('predictions.id', ondelete='CASCADE'), nullable=False, unique=True)
    is_accurate = Column(Boolean, nullable=False)
    submitted_at = Column(DateTime, default=func.now())
    
    # Relationship
    prediction = relationship('Prediction', back_populates='feedback')
    
    def __repr__(self):
        return f'<Feedback {self.id} for Prediction {self.prediction_id}>'
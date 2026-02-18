from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100))
    picture = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    settings = db.Column(db.Text) # Stored as JSON string
    chats = db.relationship('Chat', backref='user', lazy=True, cascade="all, delete-orphan")

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), default="Yeni Sohbet")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'user' or 'bot'
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.Text) # Stored as JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def set_sources(self, sources_list):
        self.sources = json.dumps(sources_list)

    def get_sources(self):
        return json.loads(self.sources) if self.sources else []

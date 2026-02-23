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
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    sources = db.Column(db.Text) # JSON list
    response_time = db.Column(db.Float) # In seconds
    prompt_tokens = db.Column(db.Integer)
    completion_tokens = db.Column(db.Integer)
    reference_details = db.Column(db.Text) # JSON string of list of dicts
    model_name = db.Column(db.String(255)) # e.g., "llava-1.6-mistral-7b"
    temperature = db.Column(db.Float) # e.g., 0.3
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def set_sources(self, sources_list):
        self.sources = json.dumps(sources_list)

    def get_sources(self):
        return json.loads(self.sources) if self.sources else []

    def set_reference_details(self, details_list):
        self.reference_details = json.dumps(details_list)

    def get_reference_details(self):
        return json.loads(self.reference_details) if self.reference_details else []

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="pending") # pending, resolved, ignored
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_rel = db.relationship('User', backref='reports')
    message_rel = db.relationship('Message', backref='reports')
    report_messages = db.relationship('ReportMessage', backref='report', lazy=True, cascade="all, delete-orphan", order_by="ReportMessage.timestamp")

class ReportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')

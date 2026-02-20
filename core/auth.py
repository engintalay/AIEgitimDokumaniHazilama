from authlib.integrations.flask_client import OAuth
from flask import url_for, redirect, session
from flask_login import login_user, logout_user
from core.models import db, User
import requests
import logging
import os

# Allow insecure transport for local dev (required for HTTP)
# Allow insecure transport for local dev (required for HTTP)
if os.getenv('FLASK_ENV') != 'production':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

oauth = OAuth()
logger = logging.getLogger("web_app")

def init_auth(app):
    oauth.init_app(app)
    
    # Google OAuth Configuration
    google_conf = app.config.get('GOOGLE_AUTH', {})
    
    oauth.register(
        name='google',
        client_id=google_conf.get('client_id'),
        client_secret=google_conf.get('client_secret'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

def handle_google_login():
    from flask import current_app
    config = current_app.config.get('GOOGLE_AUTH', {})
    
    manual_uri = config.get('redirect_uri')
    if manual_uri:
        redirect_uri = manual_uri
    else:
        redirect_uri = url_for('auth_callback', _external=True)
        
    logger.info(f"Oauth Redirect URI: {redirect_uri}")
    return oauth.google.authorize_redirect(redirect_uri)

def handle_google_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if user_info:
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')
        
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update info if changed
            user.name = name
            user.picture = picture
            user.email = email
            db.session.commit()
            
        login_user(user)
        
        # Admin promotion check
        admin_email = os.getenv('ADMIN_EMAIL', 'engintalay@gmail.com')
        if email == admin_email and not user.is_admin:
            user.is_admin = True
            db.session.commit()
            
        return True
    return False

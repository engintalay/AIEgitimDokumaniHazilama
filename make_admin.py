from app import app
from core.models import db, User

with app.app_context():
    user = User.query.filter_by(email='engintalay@gmail.com').first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"User {user.email} is now an admin.")
    else:
        print("User engintalay@gmail.com not found in database.")

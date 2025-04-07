from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin_user(username, email, password):
    with app.app_context():
        # Check if admin already exists
        if User.query.filter_by(role='admin').first():
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='admin'
        )
        
        try:
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")

if __name__ == '__main__':
    create_admin_user('admin', 'admin@example.com', 'admin123')

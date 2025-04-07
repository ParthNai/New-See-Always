from app import app, db
from models import User, Student
from werkzeug.security import generate_password_hash

def create_student_user(username, email, password, roll_number, name, course):
    with app.app_context():
        # Create user account
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='student'
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create student profile
            student = Student(
                user_id=user.id,
                roll_number=roll_number,
                name=name,
                course=course
            )
            
            db.session.add(student)
            db.session.commit()
            print("Student account created successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating student account: {e}")

if __name__ == '__main__':
    create_student_user(
        username='student',
        email='student@example.com',
        password='student123',
        roll_number='2025001',
        name='Test Student',
        course='Computer Science'
    )

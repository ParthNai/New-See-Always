from flask import Flask, render_template, request, redirect, url_for, flash
from forms import RegistrationForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import db and models
from models import db, User, Student, Faculty, Course, Attendance

# Initialize SQLAlchemy with app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create database tables
def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

# Initialize database on startup
init_db()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
            
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data,
                   email=form.email.data,
                   password=hashed_password,
                   role=form.role.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create student profile if role is student
            if form.role.data == 'student':
                student = Student(user_id=user.id,
                                name=form.username.data,
                                email=form.email.data)
                db.session.add(student)
                db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f'Registration error: {str(e)}')
    
    return render_template('register.html', form=form)

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied. Student access only.', 'danger')
        return redirect(url_for('index'))
    
    # Get student details
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('index'))
    
    # Get recent attendance records
    attendance_records = []
    try:
        attendance_records = (
            db.session.query(
                Attendance,
                Course.name.label('course'),
                Faculty.name.label('faculty_name')
            )
            .join(Course, Attendance.course_id == Course.id)
            .join(Faculty, Attendance.marked_by == Faculty.id)
            .filter(Attendance.student_id == student.id)
            .order_by(Attendance.date.desc())
            .limit(10)
            .all()
        )
    except Exception as e:
        print(f"Error fetching attendance: {e}")
    
    # Format attendance records
    records = []
    for record in attendance_records:
        records.append({
            'date': record.Attendance.date.strftime('%Y-%m-%d'),
            'course': record.course,
            'status': record.Attendance.status,
            'faculty_name': record.faculty_name
        })
    
    return render_template('student/dashboard.html', 
                         student=student, 
                         attendance_records=records)

if __name__ == '__main__':
    app.run(debug=True)

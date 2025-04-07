from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Student, Faculty, Course, Attendance
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'faculty':
                return redirect(url_for('faculty_dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('parent_dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    return render_template('admin/dashboard.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard_route():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    total_students = User.query.filter_by(role='student').count()
    return render_template('admin/dashboard.html', total_students=total_students)

@app.route('/faculty')
@login_required
def faculty_dashboard():
    if current_user.role != 'faculty':
        return redirect(url_for('index'))
    return render_template('faculty/dashboard.html')

@app.route('/faculty/dashboard')
@login_required
def faculty_dashboard_route():
    if current_user.role != 'faculty':
        flash('Access denied. Faculty privileges required.')
        return redirect(url_for('index'))
    return render_template('faculty/dashboard.html')

@app.route('/student')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))
    return render_template('student/dashboard.html')

@app.route('/student/dashboard')
@login_required
def student_dashboard_route():
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.')
        return redirect(url_for('index'))
    return render_template('student/dashboard.html')

@app.route('/parent')
@login_required
def parent_dashboard():
    if current_user.role != 'parent':
        return redirect(url_for('index'))
    return render_template('parent/dashboard.html')

@app.route('/mark-attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    if current_user.role != 'faculty':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        student_id = request.form.get('student_id')
        status = request.form.get('status')
        
        attendance = Attendance(
            student_id=student_id,
            course_id=course_id,
            status=status,
            marked_by=current_user.id,
            date=datetime.now().date()
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Attendance marked successfully')
        
    return render_template('faculty/mark_attendance.html')

@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('admin_dashboard'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists')
        return redirect(url_for('admin_dashboard'))
    
    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    
    # Create role-specific records
    if role == 'student':
        student = Student(
            user_id=user.id,
            roll_number=request.form.get('roll_number'),
            name=request.form.get('name'),
            course=request.form.get('course')
        )
        db.session.add(student)
    elif role == 'faculty':
        faculty = Faculty(
            user_id=user.id,
            name=request.form.get('name'),
            department=request.form.get('department')
        )
        db.session.add(faculty)
    
    try:
        db.session.commit()
        flash('User created successfully')
    except Exception as e:
        db.session.rollback()
        flash('Error creating user')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete admin user')
        return redirect(url_for('admin_dashboard'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully')
    except:
        db.session.rollback()
        flash('Error deleting user')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_user/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    email = request.form.get('email')
    
    if User.query.filter(User.email == email, User.id != user_id).first():
        flash('Email already exists')
        return redirect(url_for('admin_dashboard'))
    
    user.email = email
    if request.form.get('password'):
        user.password = generate_password_hash(request.form.get('password'))
    
    try:
        db.session.commit()
        flash('User updated successfully')
    except:
        db.session.rollback()
        flash('Error updating user')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users')
@login_required
def list_users():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def add_new_user():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        name = request.form.get('name')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('add_new_user'))
        
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role=role
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('User added successfully!')
        except:
            db.session.rollback()
            flash('Error adding user')
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_user.html')

@app.route('/admin/users/bulk-upload', methods=['GET', 'POST'])
@login_required
def bulk_upload_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(url_for('bulk_upload_users'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(url_for('bulk_upload_users'))
        
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file')
            return redirect(url_for('bulk_upload_users'))
        
        try:
            # Process CSV file
            import csv
            import io
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_data = csv.DictReader(stream)
            
            for row in csv_data:
                user = User(
                    username=row['username'],
                    email=row['email'],
                    password=generate_password_hash(row['password']),
                    role=row['role']
                )
                db.session.add(user)
            
            db.session.commit()
            flash('Users imported successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error importing users: {str(e)}')
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/bulk_upload.html')

@app.route('/admin/users/manage')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/results/upload', methods=['GET', 'POST'])
@login_required
def upload_results():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(url_for('upload_results'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(url_for('upload_results'))
        
        try:
            # Process results file
            flash('Results uploaded successfully!')
        except Exception as e:
            flash(f'Error uploading results: {str(e)}')
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/upload_results.html')

@app.route('/admin/results/view')
@login_required
def view_results():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    results = []  # Get results from database
    return render_template('admin/view_results.html', results=results)

@app.route('/admin/departments/search', methods=['GET', 'POST'])
@login_required
def search_departments():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        search_term = request.form.get('search')
        departments = []  # Search departments in database
        return render_template('admin/departments.html', departments=departments)
    
    departments = []  # Get all departments
    return render_template('admin/departments.html', departments=departments)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Student, Faculty, Course, Attendance
from datetime import datetime
import pandas as pd
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

# Define faculty members
FACULTY_MEMBERS = [
    {"username": "SJC", "name": "S. J. Chauhan", "department": "EC"},
    {"username": "MKP", "name": "M. K. Patel", "department": "EC"},
    {"username": "LKP", "name": "L. K. Patel", "department": "ICT"},
    {"username": "RNP", "name": "R. N. Patel", "department": "EC"},
    {"username": "MJD", "name": "M. J. Darji", "department": "ICT"},
    {"username": "RCP", "name": "R. C. Patel", "department": "EC"},
    {"username": "SPJ", "name": "S. P. Joshi", "department": "ICT"},
    {"username": "NJC", "name": "N. J. Chauhan", "department": "ICT"}
]

# Faculty timetables
FACULTY_TIMETABLES = {
    'SJC': [
        {"Time": "10:30 TO 11:30", "Subject": "IPDC(SJC)(B-009)", "Day": "FRIDAY"},
        {"Time": "11:30 TO 12:30", "Subject": "CEM(SJC)(B-008)", "Day": "MONDAY"},
        {"Time": "11:30 TO 12:30", "Subject": "IPDC(SJC)(B-009)", "Day": "FRIDAY"},
        {"Time": "1:00 TO 2:00", "Subject": "IPDC(SJC)(B-109)", "Day": "MONDAY"},
        {"Time": "1:00 TO 2:00", "Subject": "CEM(SJC)4A1(B-105)", "Day": "TUESDAY"},
        {"Time": "1:00 TO 2:00", "Subject": "CEM(SJC)(B-011)", "Day": "WEDNESDAY"},
        {"Time": "2:00 TO 3:00", "Subject": "IPDC(SJC)(B-109)", "Day": "MONDAY"},
        {"Time": "3:00 TO 4:00", "Subject": "CEM(SJC)(B-011)", "Day": "THURSDAY"}
    ]
}

def create_initial_faculty():
    """Create initial faculty users if they don't exist"""
    try:
        print("Starting initialization...")
        
        # First create faculty users
        for faculty_data in FACULTY_MEMBERS:
            username = faculty_data["username"]
            faculty_user = User.query.filter_by(username=username).first()
            if not faculty_user:
                print(f"Creating faculty user: {username}")
                faculty_user = User(
                    username=username,
                    email=f"{username.lower()}@example.com",
                    role='faculty'
                )
                faculty_user.set_password('faculty123')
                db.session.add(faculty_user)
                db.session.flush()
                
                faculty = Faculty(
                    user_id=faculty_user.id,
                    name=faculty_data["name"],
                    department=faculty_data["department"]
                )
                db.session.add(faculty)
                db.session.flush()
                print(f"Created faculty: {faculty.name}")
        
        db.session.commit()
        print("Faculty users created successfully")
        
        # Now create test student user
        student_enrollment = "236260332038"
        student_user = User.query.filter_by(username=student_enrollment).first()
        print(f"Existing student user: {student_user}")
        
        if not student_user:
            print("Creating new student user...")
            # Create user account
            student_user = User(
                username=student_enrollment,
                email="student@test.com",
                role='student'
            )
            student_user.set_password('student123')
            db.session.add(student_user)
            db.session.flush()
            print(f"Created user with ID: {student_user.id}")
            
            # Create student record
            student = Student(
                user_id=student_user.id,
                roll_number=student_enrollment,
                name="PANCHAL NISHTHABEN YOGESHBHAI",
                course='B.Tech'
            )
            db.session.add(student)
            db.session.flush()
            print(f"Created student record with ID: {student.id}")
            
            # Create sample courses and attendance
            courses = [
                {'name': 'IPDC', 'faculty': 'SJC'},
                {'name': 'CEM', 'faculty': 'SJC'},
                {'name': 'Python Programming', 'faculty': 'MJD'}
            ]
            
            for course_data in courses:
                print(f"Processing course: {course_data['name']}")
                course = Course.query.filter_by(name=course_data['name']).first()
                if not course:
                    faculty = Faculty.query.join(User).filter(User.username == course_data['faculty']).first()
                    print(f"Found faculty: {faculty.name if faculty else 'None'}")
                    course = Course(name=course_data['name'], faculty_id=faculty.id if faculty else None)
                    db.session.add(course)
                    db.session.flush()
                    print(f"Created course with ID: {course.id}")
                    
                    # Add sample attendance records
                    from datetime import datetime, timedelta
                    today = datetime.now()
                    for i in range(10):  # Last 10 days
                        date = today - timedelta(days=i)
                        # Randomly mark present or absent (more present than absent)
                        status = 'present' if i % 3 != 0 else 'absent'
                        attendance = Attendance(
                            student_id=student.id,
                            course_id=course.id,
                            date=date,
                            status=status,
                            marked_by=faculty.name if faculty else 'System'
                        )
                        db.session.add(attendance)
            
            db.session.commit()
            print("Successfully created student and attendance records")
        
        return True
    except Exception as e:
        print(f"Error in create_initial_faculty: {str(e)}")
        db.session.rollback()
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):  
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

@app.route('/faculty/login', methods=['GET', 'POST'])
def faculty_login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated and current_user.role == 'faculty':
        return redirect(url_for('faculty_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if username exists in faculty members
        faculty = next((f for f in FACULTY_MEMBERS if f["username"] == username.upper()), None)
        
        if faculty:
            # Check if user exists in database
            user = User.query.filter_by(username=username.upper()).first()
            
            if user and user.check_password(password):
                login_user(user)
                flash(f'Welcome, {faculty["name"]}!', 'success')
                return redirect(url_for('faculty_dashboard'))
            elif user:
                # User exists but wrong password
                flash('Invalid password. Please try again.', 'error')
            else:
                # First time login - create new user
                try:
                    user = User(
                        username=username.upper(),
                        email=f"{username.lower()}@gppalanpur.ac.in",
                        role='faculty'
                    )
                    user.set_password(password)
                    db.session.add(user)
                    db.session.flush()  
                    
                    # Create faculty record
                    faculty_record = Faculty(
                        user_id=user.id,
                        name=faculty["name"],
                        department=faculty["department"]
                    )
                    db.session.add(faculty_record)
                    db.session.commit()
                    
                    # Log in the new user
                    login_user(user)
                    flash(f'Welcome, {faculty["name"]}! Your account has been created.', 'success')
                    return redirect(url_for('faculty_dashboard'))
                except Exception as e:
                    db.session.rollback()
                    print(f"Error creating faculty account: {str(e)}")
                    flash('Error creating faculty account. Please try again.', 'error')
        else:
            flash('Invalid username. Please try again.', 'error')
    
    return render_template('faculty/login.html')

@app.route('/faculty/timetable/<date>')
@login_required
def get_faculty_timetable(date):
    """Get faculty timetable for a specific date"""
    if current_user.role != 'faculty':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Convert date string to datetime
        target_date = datetime.strptime(date, '%Y-%m-%d')
        day = target_date.strftime('%A').upper()
        
        # Get timetable for the faculty
        timetable = []
        if current_user.username in FACULTY_TIMETABLES:
            timetable = [slot for slot in FACULTY_TIMETABLES[current_user.username] if slot['Day'] == day]
            timetable.sort(key=lambda x: x['Time'])
        
        return jsonify({
            'timetable': timetable,
            'date': date,
            'day': day
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/faculty')
@app.route('/faculty/dashboard')
@login_required
def faculty_dashboard():
    if current_user.role != 'faculty':
        flash('Access denied. Faculty privileges required.', 'error')
        return redirect(url_for('index'))
    
    faculty = Faculty.query.filter_by(user_id=current_user.id).first()
    if not faculty:
        flash('Faculty profile not found.', 'error')
        return redirect(url_for('index'))
    
    # Get students based on faculty's department
    students = []
    if faculty.department == 'EC':
        students = [
            {"enrollment": "236260311001", "name": "CHAUDHARI RAVINDRABHAI MADRUPBHAI"},
            {"enrollment": "236260311002", "name": "DAVE FALGUNI JITENDRAKUMAR"},
            {"enrollment": "236260311003", "name": "MALI PARESHBHAI RAMESHBHAI"},
            {"enrollment": "236260311004", "name": "PATEL PRIYALBEN JAYPRAKASH"},
            {"enrollment": "236260311006", "name": "PRAJAPATI PRINCEKUMAR DILIPBHAI"},
            {"enrollment": "236260311007", "name": "PRAJAPATI SHAILESHBHAI CHELABHAI"},
            {"enrollment": "236268311001", "name": "SHRIMALI HITENKUMAR VASANTBHAI"}
        ]
    else:
        students = [
            {"enrollment": "236260332001", "name": "ACHARYA MILAP MUKESHBHAI"},
            {"enrollment": "236260332004", "name": "BHAVSAR PRACHI SNEHALKUMAR"},
            {"enrollment": "236260332006", "name": "CHANDARANA HARSHKUMAR CHANDRAKANTBHAI"}
        ]
    
    # Get today's timetable for the faculty
    today = datetime.now()
    day = today.strftime('%A').upper()
    timetable = []
    if current_user.username in FACULTY_TIMETABLES:
        timetable = [slot for slot in FACULTY_TIMETABLES[current_user.username] if slot['Day'] == day]
        timetable.sort(key=lambda x: x['Time'])
    
    return render_template('faculty/dashboard.html', 
                         faculty=faculty,
                         students=students,
                         timetable=timetable,
                         today=today.strftime('%Y-%m-%d'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    # Get student details
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get attendance records
    attendance_records = db.session.query(
        Attendance, Course
    ).join(
        Course, Course.id == Attendance.course_id
    ).filter(
        Attendance.student_id == student.id
    ).order_by(
        Attendance.date.desc()
    ).all()
    
    # Calculate attendance statistics
    attendance_stats = {}
    for record, course in attendance_records:
        if course.name not in attendance_stats:
            attendance_stats[course.name] = {
                'total': 0,
                'present': 0,
                'absent': 0
            }
        
        attendance_stats[course.name]['total'] += 1
        if record.status == 'present':
            attendance_stats[course.name]['present'] += 1
        else:
            attendance_stats[course.name]['absent'] += 1
    
    # Calculate percentages
    for course in attendance_stats:
        total = attendance_stats[course]['total']
        if total > 0:
            percentage = (attendance_stats[course]['present'] / total) * 100
            attendance_stats[course]['percentage'] = round(percentage, 2)
            # Add grade based on percentage
            if percentage >= 80:
                attendance_stats[course]['grade'] = 'A'
            elif percentage >= 70:
                attendance_stats[course]['grade'] = 'B'
            elif percentage >= 60:
                attendance_stats[course]['grade'] = 'C'
            else:
                attendance_stats[course]['grade'] = 'D'
    
    return render_template(
        'student/dashboard.html',
        student=student,
        attendance_stats=attendance_stats,
        attendance_records=attendance_records
    )

@app.route('/student/update-password', methods=['POST'])
@login_required
def update_student_password():
    if current_user.role != 'student':
        return jsonify({'error': 'Access denied!'}), 403
    
    new_password = request.form.get('new_password')
    if not new_password:
        return jsonify({'error': 'New password is required!'}), 400
    
    # Update password
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password updated successfully!'}), 200

@app.route('/parent')
@login_required
def parent_dashboard():
    if current_user.role != 'parent':
        return redirect(url_for('index'))
    return render_template('parent/dashboard.html')

@app.route('/mark-attendance', methods=['POST'])
@login_required
def mark_attendance():
    if current_user.role != 'faculty':
        flash('Access denied. Faculty privileges required.')
        return redirect(url_for('index'))
    
    course = request.form.get('course')
    if not course:
        flash('Please select a course')
        return redirect(url_for('faculty_dashboard'))

    # Get the current date
    current_date = datetime.now().date()
    
    # Get all form data
    attendance_data = []
    for key, value in request.form.items():
        if key.startswith('status_'):
            enrollment = key.replace('status_', '')
            attendance_data.append({
                'enrollment': enrollment,
                'status': value,
                'date': current_date
            })
    
    try:
        # Here you would typically save this to your database
        # For now, we'll just show a success message
        flash(f'Attendance marked successfully for {course.upper()} department')
    except Exception as e:
        flash('Error marking attendance: ' + str(e))
    
    return redirect(url_for('faculty_dashboard'))

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
    
    results = []  
    return render_template('admin/view_results.html', results=results)

@app.route('/admin/departments/search', methods=['GET', 'POST'])
@login_required
def search_departments():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        search_term = request.form.get('search')
        departments = []  
        return render_template('admin/departments.html', departments=departments)
    
    departments = []  
    return render_template('admin/departments.html', departments=departments)

@app.route('/admin/courses')
@login_required
def admin_courses():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    ec_students = [
        {"enrollment": "236260311001", "name": "CHAUDHARI RAVINDRABHAI MADRUPBHAI"},
        {"enrollment": "236260311002", "name": "DAVE FALGUNI JITENDRAKUMAR"},
        {"enrollment": "236260311003", "name": "MALI PARESHBHAI RAMESHBHAI"},
        {"enrollment": "236260311004", "name": "PATEL PRIYALBEN JAYPRAKASH"},
        {"enrollment": "236260311006", "name": "PRAJAPATI PRINCEKUMAR DILIPBHAI"},
        {"enrollment": "236260311007", "name": "PRAJAPATI SHAILESHBHAI CHELABHAI"},
        {"enrollment": "236268311001", "name": "SHRIMALI HITENKUMAR VASANTBHAI"}
    ]
    
    ict_students = [
        {"enrollment": "236260332001", "name": "ACHARYA MILAP MUKESHBHAI"},
        {"enrollment": "236260332004", "name": "BHAVSAR PRACHI SNEHALKUMAR"},
        {"enrollment": "236260332006", "name": "CHANDARANA HARSHKUMAR CHANDRAKANTBHAI"},
        {"enrollment": "236260332007", "name": "CHAROLIYA MAYSAMALI ARIDALI"},
        {"enrollment": "236260332008", "name": "CHAUDHARI SHAILESHBHAI RAMESHBHAI"},
        {"enrollment": "236260332018", "name": "GAJJAR DEVANGSHI PRAKISHBHAI"},
        {"enrollment": "236260332020", "name": "GAUSWAMI JAYESHBHAI ASHOKBHAI"},
        {"enrollment": "236260332021", "name": "GHASURA HAMZA MAHAMAD ARIF"},
        {"enrollment": "236260332022", "name": "GOHIL TRUPTI ALPESHBHAI"},
        {"enrollment": "236260332024", "name": "JASALIYA SHRADDHDHA ASHOKBHAI"},
        {"enrollment": "236260332028", "name": "KURESHI MAHAMMADSEZAM SADIKBHAI"},
        {"enrollment": "236260332029", "name": "MAMDNIYA ARMAN IMRANBHAI"},
        {"enrollment": "236260332030", "name": "MEVADA AAHYKUMAR MUKESHKUMAR"},
        {"enrollment": "236260332031", "name": "MEVADA DIVYA VIPULBHAI"},
        {"enrollment": "236260332033", "name": "MODI CHARU BHARATKUMAR"},
        {"enrollment": "236260332034", "name": "MODI HARSHIL MAHENDRAKUMAR"},
        {"enrollment": "236260332035", "name": "NAI PARTH ANILBHAI"},
        {"enrollment": "236260332038", "name": "PANCHAL NISHTHABEN YOGESHBHAI"},
        {"enrollment": "236260332039", "name": "PANCHAL POOJA NAVINBHAI"},
        {"enrollment": "236260332040", "name": "PARHADIYA IMRANBHAI HAMIDBHAI"},
        {"enrollment": "236260332041", "name": "PARMAR DHAVALKUMAR DAHYABHAI"},
        {"enrollment": "236260332042", "name": "PARMAR KRUSHNAKPALSINH VIJAYSINH"},
        {"enrollment": "236260332043", "name": "PATEL HEET HARESHBHAI"},
        {"enrollment": "236260332045", "name": "PATEL MANISHBEN SHAILESHBHAI"},
        {"enrollment": "236260332047", "name": "PATEL SAURAV NEETABEN RAJESHBHAI"},
        {"enrollment": "236260332056", "name": "RAVAL DEV SURESHKUMAR"},
        {"enrollment": "236260332059", "name": "SUTHAR ANIL KUMAR HARESH BHAI"},
        {"enrollment": "236260332060", "name": "THAKKAR DARSHAN JAGDISHBHAI"},
        {"enrollment": "236260332061", "name": "THAKOR RIDHI RAMESHJI"},
        {"enrollment": "236260332005", "name": "CHAUHAN PRUTHVI VIRALKUMAR"},
        {"enrollment": "236260332009", "name": "MENAT TANISH SOMABHAI"},
        {"enrollment": "236260332023", "name": "SHEIKH ZIDAN SADIKAHAMAD"},
        {"enrollment": "236260332024", "name": "SOLANKI KRISH SURESHBHAI"},
        {"enrollment": "236260332029", "name": "VYASG KAUSHIK A"}
    ]
    
    return render_template('admin/courses.html', ec_students=ec_students, ict_students=ict_students)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Student Registration and Dashboard Routes
@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        enrollment = request.form.get('enrollment')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if student already exists
        existing_student = Student.query.filter_by(roll_number=enrollment).first()
        if existing_student:
            flash('Student with this enrollment number already exists!', 'error')
            return redirect(url_for('student_register'))
        
        # Create user account
        user = User(
            username=enrollment,
            email=email,
            role='student'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user.id before committing
        
        # Create student record
        student = Student(
            user_id=user.id,
            roll_number=enrollment,
            name=name,
            course='B.Tech'  # You can make this dynamic based on your needs
        )
        db.session.add(student)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('student/register.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_initial_faculty()  
    app.run(debug=True)

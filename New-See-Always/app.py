from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Parent(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    students = db.relationship('Student', backref='parent', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    attendance = db.Column(db.Float, default=0.0)
    current_cgpa = db.Column(db.Float, default=0.0)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'), nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Parent.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if Parent.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        parent = Parent(email=email, password=hashed_password)
        db.session.add(parent)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    portal_type = request.args.get('type', 'parent')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if portal_type == 'admin':
            user = Parent.query.filter_by(email=email, is_admin=True).first()
        elif portal_type == 'parent':
            user = Parent.query.filter_by(email=email).first()
        elif portal_type == 'faculty':
            user = Faculty.query.filter_by(email=email).first()
        else:
            flash('Invalid portal type')
            return redirect(url_for('login'))
        
        if user and check_password_hash(user.password, password):
            if isinstance(user, Parent):
                login_user(user)
                return redirect(url_for('admin_dashboard' if user.is_admin else 'dashboard'))
            elif isinstance(user, Faculty):
                # Implement faculty login logic
                return redirect(url_for('faculty_dashboard'))
        flash('Invalid email or password')
    return render_template('login.html', portal_type=portal_type)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', students=current_user.students)

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    parents = Parent.query.all()
    students = Student.query.all()
    return render_template('admin_dashboard.html', parents=parents, students=students)

@app.route('/admin/make_admin/<int:user_id>')
@login_required
@admin_required
def make_admin(user_id):
    user = Parent.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'Made {user.email} an admin')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/remove_admin/<int:user_id>')
@login_required
@admin_required
def remove_admin(user_id):
    if user_id != current_user.id:
        user = Parent.query.get_or_404(user_id)
        user.is_admin = False
        db.session.commit()
        flash(f'Removed admin privileges from {user.email}')
    else:
        flash('You cannot remove your own admin privileges')
    return redirect(url_for('admin_dashboard'))

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form.get('name')
        roll_number = request.form.get('roll_number')
        branch = request.form.get('branch')
        semester = request.form.get('semester')
        
        student = Student(
            name=name,
            roll_number=roll_number,
            branch=branch,
            semester=semester,
            parent=current_user
        )
        db.session.add(student)
        db.session.commit()
        flash('Student added successfully')
        return redirect(url_for('dashboard'))
    return render_template('add_student.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

def create_sample_data():
    # Branch data
    branches = ['ICT', 'EC', 'IT', 'CIVIL', 'MECHANICAL', 'ELECTRICAL']
    indian_names = [
        'Aarav', 'Arjun', 'Dev', 'Ishaan', 'Kabir', 'Neel', 'Om', 'Reyansh', 'Veer', 'Yash',
        'Aanya', 'Diya', 'Ira', 'Kiara', 'Myra', 'Pari', 'Riya', 'Saanvi', 'Tara', 'Zara'
    ]
    
    # Create sample students for each branch
    for branch in branches:
        # Create 5 students per branch
        for i in range(5):
            name = random.choice(indian_names)
            roll_number = f"{branch[:2]}{str(random.randint(1, 99)).zfill(2)}"
            semester = random.randint(1, 8)
            attendance = random.uniform(75.0, 98.0)
            cgpa = random.uniform(6.0, 9.5)
            
            # Create a parent for the student
            parent_email = f"parent_{branch.lower()}_{i+1}@example.com"
            parent = Parent(
                email=parent_email,
                password=generate_password_hash('password123')
            )
            db.session.add(parent)
            db.session.commit()
            
            # Create the student
            student = Student(
                name=name,
                roll_number=roll_number,
                branch=branch,
                semester=semester,
                attendance=attendance,
                current_cgpa=cgpa,
                parent_id=parent.id
            )
            db.session.add(student)
    
    # Create faculty members
    for branch in branches:
        faculty = Faculty(
            email=f"faculty_{branch.lower()}@example.com",
            password=generate_password_hash('faculty123'),
            name=f"Prof. {random.choice(indian_names)}",
            department=branch
        )
        db.session.add(faculty)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        admin = Parent.query.filter_by(email='admin@admin.com').first()
        if not admin:
            admin = Parent(
                email='admin@admin.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            
            # Create sample data only if admin was just created
            create_sample_data()
            
    app.run(debug=True)

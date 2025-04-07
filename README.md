# Student Attendance Management System

A web-based attendance management system with multiple user roles:
- Admin: Complete system control
- Faculty: Manage lecture attendance
- Students: View their attendance
- Parents: Monitor their child's attendance

## Features
- Multi-user role system
- Real-time attendance tracking
- Secure authentication
- Responsive dashboard for each user type
- Admin panel for system management

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

3. Run the application:
```bash
python app.py
```

## Access
- Admin Portal: /admin
- Faculty Portal: /faculty
- Student Portal: /student
- Parent Portal: /parent

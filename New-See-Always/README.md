# See Your Child Always

A web application that helps parents monitor their college students' academic progress.

## Features

- Parent registration and login system
- Add and monitor multiple students
- Track student attendance
- Monitor CGPA
- Last seen status
- Responsive design for all devices

## Installation

1. Clone the repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Technologies Used

- Python Flask
- SQLAlchemy
- Flask-Login
- Bootstrap 5
- SQLite Database

## Project Structure

```
.
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── templates/         # HTML templates
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── add_student.html
└── site.db           # SQLite database (created automatically)
```

import mysql.connector
import os

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Ian.5960',
    'database': 'housing_management'
}

# Establish DB connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Upload config
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Use a static secret key (don't generate on every run)
SECRET_KEY = "your_very_secret_and_long_key_here"  # Replace with your secure string


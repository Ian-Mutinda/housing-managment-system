from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import jwt
import datetime
from functools import wraps
import os
from config import get_db_connection, SECRET_KEY, UPLOAD_FOLDER, allowed_file
from flask_cors import CORS

auth_bp = Blueprint('auth', __name__)
CORS(auth_bp)  # Allow cross-origin requests for auth routes


def create_user(name, username, email, password, role):
    hashed_password = generate_password_hash(password)
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE email = %s OR username = %s", (email, username))
        if cursor.fetchone():
            return "User already exists"

        cursor.execute("INSERT INTO users (name, username, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                       (name, username, email, hashed_password, role))
        connection.commit()
        return True
    except Exception as e:
        print(f"Database Error: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(" ")[1]  # Remove 'Bearer' prefix
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)

    return decorated


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json

    # Ensure all required fields exist
    required_fields = ("name", "username", "email", "password", "role")
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing fields"}), 400

    result = create_user(data["name"], data["username"], data["email"], data["password"], data["role"])
    
    if result == "User already exists":
        return jsonify({"message": "User with this email or username already exists"}), 409  # Conflict
    
    if result:
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"message": "User registration failed"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)

    # Ensure request contains required fields
    if not data or "email" not in data or "password" not in data:
        return jsonify({"message": "Email and password are required"}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (data["email"],))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user:
        return jsonify({"message": "User not found"}), 404  # Return user not found if no matching email

    if not check_password_hash(user['password'], data['password']):
        return jsonify({"message": "Invalid credentials"}), 401  # Invalid password

    token = jwt.encode({
        "user_id": user['id'],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({"token": token, "role": user["role"]}), 200


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    return jsonify({"message": "Logged out successfully"}), 200


# ------------------ NEW: Upload Profile Picture ------------------ #
@auth_bp.route('/upload_profile_pic', methods=['POST'])
@token_required
def upload_profile_pic():
    user_id = request.user_id

    if 'profile_pic' not in request.files:
        return jsonify({"message": "No file part in request"}), 400

    file = request.files['profile_pic']

    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(f"user_{user_id}_" + file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET profile_picture = %s WHERE id = %s", (filename, user_id))
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"message": "Profile picture uploaded successfully", "filename": filename}), 200
    else:
        return jsonify({"message": "Invalid file type"}), 400


# ------------------ NEW: Get Profile Picture ------------------ #
@auth_bp.route('/profile_pictures/<filename>')
def get_profile_picture(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)





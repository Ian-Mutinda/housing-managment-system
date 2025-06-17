from flask import Blueprint, request, jsonify, render_template, current_app
from config import get_db_connection
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint('admin', __name__)

# ✅ Fixed: renamed function to avoid name conflict
@admin_bp.route('/dashboard')
def dashboard_view():
    return render_template('admin.html')

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, username, email, role FROM users")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(users), 200
@admin_bp.route('/admin/client-users', methods=['GET'])
def get_client_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # Join users with their latest payment and properties
        cur.execute("""
            SELECT 
                u.id, 
                u.username AS name, 
                u.email,
                p.title AS property_title,
                pay.amount,
                pay.status AS payment_status,
                pay.due_date
            FROM users u
            LEFT JOIN properties p ON u.property_id = p.id
            LEFT JOIN (
                SELECT * FROM payments 
                WHERE (user_id, payment_date) IN (
                    SELECT user_id, MAX(payment_date)
                    FROM payments
                    GROUP BY user_id
                )
            ) AS pay ON u.id = pay.user_id
            WHERE u.role != 'admin'
        """)
        users = cur.fetchall()

        conn.close()
        return jsonify(users), 200

    except Exception as e:
        print("Error fetching client users:", e)
        return jsonify({"error": "Internal server error"}), 500



@admin_bp.route('/bookings/<int:booking_id>', methods=['PUT'])
def update_booking_status(booking_id):
    data = request.json
    new_status = data.get("status")
    if new_status not in ["approved", "rejected"]:
        return jsonify({"message": "Invalid status"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE bookings SET status = %s WHERE id = %s", (new_status, booking_id))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Booking status updated successfully"}), 200

@admin_bp.route('/payments', methods=['GET'])
def get_all_payments():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM payments")
    payments = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(payments), 200

@admin_bp.route('/properties', methods=['POST'])
def add_property():
    data = request.json
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO properties (name, location, price, status) VALUES (%s, %s, %s, 'available')",
                   (data['name'], data['location'], data['price']))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Property added successfully"}), 201

@admin_bp.route('/properties', methods=['GET'])
def get_all_properties():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM properties")
    properties = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(properties), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "User deleted"}), 200

@admin_bp.route('/properties/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM properties WHERE id = %s", (property_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Property deleted"}), 200

@admin_bp.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    filename = secure_filename(file.filename)
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))

    return jsonify({"message": "Image uploaded", "filename": filename}), 200

# ✅ New: community.html route
@admin_bp.route('/community')
def community_view():
    return render_template('community.html')




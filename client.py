from flask import Blueprint, request, jsonify, render_template, send_file
from config import get_db_connection
from auth import token_required
import os
from werkzeug.utils import secure_filename
from flask import session


client_bp = Blueprint('client', __name__)

# ✅ Dashboard Page Route
@client_bp.route('/dashboard')
def client_dashboard():
    return render_template("client_dashboard.html")

@client_bp.route('/client/community')
def client_community():
    messages = get_all_messages()  # or however you load messages
    return render_template('client_communication.html', messages=messages)


# ✅ Get Available Properties
@client_bp.route('/properties', methods=['GET'])
@token_required
def get_properties():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM properties WHERE available = 1")
    properties = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(properties), 200

# ✅ Book a Property
@client_bp.route('/book', methods=['POST'])
@token_required
def book_property():
    data = request.json
    user_id = request.user_id
    property_id = data.get('property_id')

    if not property_id:
        return jsonify({"message": "Property ID is required"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT available FROM properties WHERE id = %s", (property_id,))
        property_info = cursor.fetchone()

        if not property_info or not property_info[0]:
            return jsonify({"message": "Property not available"}), 400

        cursor.execute("INSERT INTO bookings (user_id, property_id) VALUES (%s, %s)", (user_id, property_id))
        cursor.execute("UPDATE properties SET available = 0 WHERE id = %s", (property_id,))
        connection.commit()

        return jsonify({"message": "Property booked successfully"}), 201
    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Booking failed"}), 500
    finally:
        cursor.close()
        connection.close()

# ✅ Get Payment History
@client_bp.route('/payments', methods=['GET'])
@token_required
def get_payments():
    user_id = request.user_id
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT 
            p.id AS payment_id,
            pr.name AS property_name,
            p.amount,
            p.payment_date,
            p.status
        FROM payments p
        JOIN properties pr ON p.property_id = pr.id
        WHERE p.user_id = %s
        ORDER BY p.payment_date DESC
    """
    cursor.execute(query, (user_id,))
    payments = cursor.fetchall()

    for payment in payments:
        payment['receipt_url'] = f"/client/download_receipt/{payment['payment_id']}"
        payment['payment_date'] = payment['payment_date'].strftime('%Y-%m-%d')

    cursor.close()
    connection.close()

    return jsonify(payments), 200


# ✅ Dashboard Summary
@client_bp.route('/dashboard_summary', methods=['GET'])
@token_required
def dashboard_summary():
    user_id = request.user_id
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM rentals WHERE user_id = %s", (user_id,))
    total_properties = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS pending FROM payments WHERE user_id = %s AND status = 'pending'", (user_id,))
    pending_payments = cursor.fetchone()['pending']

    cursor.execute("SELECT COUNT(*) AS completed FROM payments WHERE user_id = %s AND status = 'completed'", (user_id,))
    completed_payments = cursor.fetchone()['completed']

    cursor.close()
    connection.close()

    return jsonify({
        "total_properties": total_properties,
        "pending_payments": pending_payments,
        "completed_payments": completed_payments
    }), 200

# ✅ Reminders
@client_bp.route('/reminders', methods=['GET'])
@token_required
def get_reminders():
    user_id = request.user_id
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.name AS property_name, r.due_date
        FROM rentals r
        JOIN properties p ON r.property_id = p.id
        WHERE r.user_id = %s AND r.due_date >= CURDATE()
        ORDER BY r.due_date ASC
        LIMIT 5
    """, (user_id,))
    reminders = cursor.fetchall()

    cursor.close()
    connection.close()
    return jsonify(reminders), 200

# ✅ Get Support Messages
@client_bp.route('/get_messages', methods=['GET'])
@token_required
def get_messages():
    user_id = request.user_id
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
         SELECT sender_id, message, sent_at 
         FROM chat_messages 
         WHERE receiver_id = %s 
         ORDER BY sent_at DESC
        LIMIT 20
    """, (user_id,))
    messages = cursor.fetchall()

    cursor.close()
    connection.close()
    return jsonify(messages), 200

# ✅ Send Support Message
@client_bp.route('/send_message', methods=['POST'])
@token_required
def send_message():
    user_id = request.user_id
    data = request.get_json()
    message = data.get("message")

    if not message:
        return jsonify({"message": "Message is required"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("INSERT INTO support_messages (user_id, sender, message) VALUES (%s, %s, %s)", 
                   (user_id, "Client", message))
    connection.commit()

    cursor.close()
    connection.close()
    return jsonify({"message": "Message sent successfully"}), 200

# ✅ Upload Profile Picture
@client_bp.route('/upload_picture', methods=['POST'])
@token_required
def upload_picture():
    user_id = request.user_id

    if 'profile_picture' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join("static", "uploads", filename)
    file.save(filepath)

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET profile_picture = %s WHERE id = %s", (filepath, user_id))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Profile picture uploaded successfully", "picture_url": f"/{filepath}"}), 200

# ✅ Download Receipt
@client_bp.route('/download_receipt/<int:payment_id>', methods=['GET'])
@token_required
def download_receipt(payment_id):
    user_id = request.user_id
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT receipt_path FROM payments WHERE id = %s AND user_id = %s", (payment_id, user_id))
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    if result and result['receipt_path'] and os.path.exists(result['receipt_path']):
        return send_file(result['receipt_path'], as_attachment=True)
    return jsonify({"message": "Receipt not found"}), 404




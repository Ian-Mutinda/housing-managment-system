# backend/community.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import get_db_connection

community_bp = Blueprint('community', __name__)

# 🔹 Get all messages
@community_bp.route('/community/messages', methods=['GET'])
def get_messages():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT cm.id, cm.sender_id, u.username AS sender, cm.message, cm.sent_at
        FROM chat_messages cm
        JOIN users u ON cm.sender_id = u.id
        ORDER BY cm.sent_at ASC
    """)
    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(messages)


# 🔹 Send a message
@community_bp.route('/community/send', methods=['POST'])
def send_message():
    data = request.get_json()
    sender_username = data.get('sender')
    message = data.get('message')

    if not sender_username or not message:
        return jsonify({'error': 'Missing sender or message'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get sender's ID
    cursor.execute("SELECT id FROM users WHERE username = %s", (sender_username,))
    sender_row = cursor.fetchone()
    if not sender_row:
        return jsonify({'error': 'Sender not found'}), 404
    sender_id = sender_row[0]

    # Insert message
    cursor.execute("""
        INSERT INTO chat_messages (sender_id, receiver_id, message, sent_at)
        VALUES (%s, NULL, %s, %s)
    """, (sender_id, message, datetime.now()))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'status': 'Message sent'}), 200

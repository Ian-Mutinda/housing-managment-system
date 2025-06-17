import os
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from auth import auth_bp
from client import client_bp
from admin import admin_bp
from community import community_bp
from config import SECRET_KEY, get_db_connection

def create_app():

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, 'static'),
        template_folder=os.path.join(base_dir, 'templates')
    )

    CORS(app)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SESSION_TYPE'] = 'filesystem'

    # Enable sessions
    from flask_session import Session
    Session(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(client_bp, url_prefix='/client')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(community_bp)

    @app.route('/')
    def home():
        return render_template("main.html")

    # 🌐 COMMUNITY CHAT ROUTES

    # ✅ Get all messages with sender name
    @app.route('/community/messages', methods=['GET'])
    def get_community_messages():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT cm.id, u.name AS sender, cm.message, cm.sent_at
            FROM chat_messages cm
            JOIN users u ON cm.sender_id = u.id
            ORDER BY cm.sent_at ASC
        """)
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(messages)
        

    # ✅ Post a new message using sender name
    @app.route('/community/send', methods=['POST'])
    def send_community_message():
        data = request.json
        sender_name = data.get("sender")
        message = data.get("message")

        if not sender_name or not message:
            return jsonify({"error": "Sender and message are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Lookup user ID from sender name
        cursor.execute("SELECT id FROM users WHERE name = %s", (sender_name,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Sender not found"}), 404

        sender_id = user["id"]

        # Insert into chat_messages
        cursor.execute(
            "INSERT INTO chat_messages (sender_id, receiver_id, message) VALUES (%s, NULL, %s)",
            (sender_id, message)
        )

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Message sent successfully"}), 201
    
    @app.route('/admin/community')
    def admin_community():
       conn = get_db_connection()
       cursor = conn.cursor(dictionary=True)
       cursor.execute("""
                   SELECT cm.id, u.name AS sender, cm.message, cm.sent_at
                   FROM chat_messages cm
                   JOIN users u ON cm.sender_id = u.id
                   ORDER BY cm.sent_at ASC
                   """)
       messages = cursor.fetchall()
       cursor.close()
       conn.close()
       return render_template('admin_community.html', messages=messages)

    
    @app.route('/client/community')
    def client_community():
        #fetch community messages from the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
                       SELECT cm.id, u.name AS sender, cm.message, cm.sent_at
                       FROM chat_messages cm
                       JOIN users u ON cm.sender_id = u.id
                       ORDER BY cm.sent_at ASC
                       """)
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
    
    

        #Rebder the community page with the fetched messages 
        return render_template('client_community.html', messages=messages)
    
    

    # ✅ Get all client users with property and payment status
    @app.route('/admin/client-users', methods=['GET'])
    def get_client_users():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT 
            u.id,
            u.name,
            u.email,
            r.property_id,
            CASE 
                WHEN COUNT(p.payment_id) = 0 THEN 'No Payments'
                WHEN MAX(p.payment_date) < CURDATE() THEN 'Pending'
                ELSE 'Paid'
            END AS payment_status
        FROM users u
        LEFT JOIN rentals r ON u.id = r.user_id
        LEFT JOIN payment p ON u.id = p.customer_id
        WHERE u.role = 'client'
        GROUP BY u.id, r.property_id
    """)

        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(users)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)






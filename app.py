import sqlite3
import json
import uuid
from flask import Flask, jsonify, request, g
from contextlib import closing
from flask_cors import CORS 
from collections import defaultdict

# --- Configuration ---
DATABASE = 'helpconnect.db'
app = Flask(__name__)
# Enable CORS for all routes so the local index.html file can access the API
CORS(app) 
app.config['DEBUG'] = True 

# --- Database Helper Functions ---

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database connection at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    """Initializes the database from the schema.sql file."""
    with app.app_context():
        db = get_db()
        try:
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()
            print("Database initialized successfully.")
        except IOError:
            print("ERROR: schema.sql not found. Cannot initialize database.")

# --- Authentication Endpoints (UNCHANGED) ---

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    required_fields = ['email', 'password', 'full_name', 'city', 'role']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required registration fields."}), 400
    
    if '@' not in data['email']:
        return jsonify({"error": "Invalid email format."}), 400

    db = get_db()
    try:
        if db.execute('SELECT id FROM profiles WHERE email = ?', (data['email'],)).fetchone():
            return jsonify({"error": "User with this email already exists."}), 409

        new_id = str(uuid.uuid4()) 
        mock_password_hash = "mock_hash" 

        hourly_rate = data.get('hourly_rate', None) if data['role'] == 'helper' else None
        skills = data.get('skills', None) if data['role'] == 'helper' else None

        db.execute("""
            INSERT INTO profiles (id, email, password_hash, role, full_name, city, state, description, skills, hourly_rate, member_since)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_id, data['email'], mock_password_hash, data['role'], data['full_name'], 
            data['city'], data.get('state'), data.get('description'), skills, hourly_rate, 2025
        ))
        db.commit()
        
        return jsonify({
            "message": "Registration successful! (Use 'password' to login)",
            "user_id": new_id,
            "role": data['role']
        }), 201
    except Exception as e:
        app.logger.error(f"Registration failed: {e}")
        return jsonify({"error": "Database error during registration."}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
        
    db = get_db()
    user = db.execute('SELECT id, role, password_hash, full_name FROM profiles WHERE email = ?', (email,)).fetchone()
    
    if not user:
        return jsonify({"error": "Invalid email or password."}), 401
        
    if user['password_hash'] == 'mock_hash' and password == 'password':
        return jsonify({
            "message": "Login successful!",
            "user_id": user['id'],
            "full_name": user['full_name'],
            "role": user['role']
        }), 200
    else:
        return jsonify({"error": "Invalid email or password."}), 401

# --- Data Endpoints (Helper Search UNCHANGED) ---

@app.route('/api/helpers', methods=['GET'])
def get_helpers():
    db = get_db()
    city = request.args.get('city', '').strip()
    skill = request.args.get('skill', '').strip()
    
    query_parts = ["SELECT * FROM profiles WHERE role = 'helper'"]
    params = []
    
    if city:
        query_parts.append(" AND city LIKE ?")
        params.append(f'%{city}%')
    
    if skill:
        query_parts.append(" AND skills LIKE ?")
        params.append(f'%{skill}%')
        
    query_parts.append(" ORDER BY rating DESC, reviews_count DESC")
    final_query = " ".join(query_parts)
    
    try:
        cur = db.execute(final_query, params)
        helpers_list = [dict(row) for row in cur.fetchall()]
        return jsonify(helpers_list)

    except Exception as e:
        app.logger.error(f"Error fetching helpers: {e}")
        return jsonify({"error": "Could not retrieve helper data."}), 500

@app.route('/api/helpers/<string:helper_id>', methods=['GET'])
def get_helper_profile(helper_id):
    db = get_db()
    profile = db.execute('SELECT * FROM profiles WHERE id = ? AND role = "helper"', (helper_id,)).fetchone()
    
    if not profile:
        return jsonify({"error": "Helper not found"}), 404
        
    profile_dict = dict(profile)
    
    avail_cur = db.execute('SELECT days, start_time, end_time FROM availabilities WHERE helper_id = ?', (helper_id,))
    profile_dict['availabilities'] = [dict(row) for row in avail_cur.fetchall()]
    
    review_cur = db.execute('SELECT r.rating, r.comment, r.created_at, p.full_name AS reviewer_name FROM reviews r JOIN profiles p ON r.reviewer_id = p.id WHERE r.reviewee_id = ? ORDER BY r.created_at DESC', (helper_id,))
    profile_dict['reviews'] = [dict(row) for row in review_cur.fetchall()]
    
    return jsonify(profile_dict)

@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.json
    required_fields = ['client_id', 'helper_id', 'scheduled_date', 'scheduled_start', 'details']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required job details."}), 400
        
    db = get_db()
    try:
        job_id = str(uuid.uuid4())
        hourly_rate = data.get('agreed_hourly_rate', 200.00)
        total_amount = data.get('total_amount', 400.00)

        db.execute("INSERT INTO jobs (id, client_id, helper_id, scheduled_date, scheduled_start, scheduled_end, agreed_hourly_rate, total_amount, status, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, data['client_id'], data['helper_id'], data['scheduled_date'], data['scheduled_start'], data['scheduled_end'], hourly_rate, total_amount, 'requested', data['details']))
        db.commit()
        return jsonify({"message": "Job request submitted successfully!", "job_id": job_id}), 201
    except Exception as e:
        app.logger.error(f"Job creation failed: {e}")
        return jsonify({"error": "Database error during job creation."}), 500


# --- Helper Dashboard Endpoints (NEW) ---

@app.route('/api/jobs/helper/<string:helper_id>', methods=['GET'])
def get_helper_jobs(helper_id):
    """Fetches all jobs for a specific helper, joining client data."""
    db = get_db()
    try:
        query = """
            SELECT 
                j.id, j.scheduled_date, j.scheduled_start, j.scheduled_end, j.details, j.status,
                p.full_name AS client_name, p.city, p.phone
            FROM jobs j
            JOIN profiles p ON j.client_id = p.id
            WHERE j.helper_id = ?
            ORDER BY j.scheduled_date DESC, j.status
        """
        cur = db.execute(query, (helper_id,))
        jobs_list = [dict(row) for row in cur.fetchall()]
        return jsonify(jobs_list)
    except Exception as e:
        app.logger.error(f"Error fetching helper jobs: {e}")
        return jsonify({"error": "Could not retrieve jobs."}), 500

@app.route('/api/jobs/<string:job_id>/status', methods=['PUT'])
def update_job_status(job_id):
    """Updates the status of a specific job (e.g., 'accepted', 'rejected', 'completed')."""
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['accepted', 'rejected', 'completed', 'cancelled']:
        return jsonify({"error": "Invalid status value."}), 400
        
    db = get_db()
    try:
        db.execute("UPDATE jobs SET status = ? WHERE id = ?", (new_status, job_id))
        db.commit()
        return jsonify({"message": f"Job {job_id} status updated to {new_status}"}), 200
    except Exception as e:
        app.logger.error(f"Error updating job status: {e}")
        return jsonify({"error": "Database error during status update."}), 500


# --- Initialization and Run ---
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)

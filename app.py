from flask import Flask, render_template, jsonify, request ,session, redirect, flash
import sqlite3 
import hashlib
app = Flask(__name__)
app.secret_key = "2321245"
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

import sqlite3

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT,
            bio TEXT,
            notifications INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
    
@app.route("/")
def home():
    return render_template("index.html")
#registration page
@app.route("/register")
def register():
    return render_template("register.html")

# Registration Route
@app.route("/register_user", methods=["POST"])
def register_user():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")
    if not all([name, email, phone, username, password, role]):
        return jsonify({"success": False, "error": "All fields are required!"})
    
    hashed_password = hash_password(password)

    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (name, email, phone, username, password, role)
                          VALUES (?, ?, ?, ?, ?, ?)''',(name, email, phone, username, hashed_password, role))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Registration successful!"})

    except sqlite3.IntegrityError as e:
        error_msg = "Email or Username already registered!"
        return jsonify({"success": False, "error": error_msg}) 
@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")

@app.route('/login_user', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"success": False, "error": "All fields are required!"})
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        user_id, stored_password = user
        if hash_password(password) == stored_password:
            session["user_id"] = user_id
            session["username"] = username
            return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid username or password!"})

@app.route('/save_profile', methods=['POST'])
def save_profile():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "User not logged in"})
    data = request.get_json()
    name = data.get("fullName")
    email = data.get("email")
    phone = data.get("phone")
    location = data.get("location")
    bio = data.get("bio")
    role = data.get("accountType")
    notifications = 1 if data.get("notifications") else 0
    if not (name and email and phone and location):
        return jsonify({"success": False, "error": "All fields are required"})

    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET name = ?, email = ?, phone = ?, location = ?, bio = ?, role = ?, notifications = ?
            WHERE id = ?""", (name, email, phone, location, bio, role, notifications, session["user_id"]))
        conn.commit()
    return jsonify({"success": True, "message": "Profile updated successfully"})

@app.route("/jobs_op", methods=["POST"])
def job_op():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401  
    try:
        data = request.get_json()
        required_fields = ["name","work", "location", "stipend", "details"]
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO  jobs (user_id, name , location, stipend, details)
                         VALUES (?, ?, ?, ?, ?)""",
                      (session["user_id"], data["name"], data["location"], data["stipend"], ))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/post-job', methods=['GET'])
def post_job_form():
    if "user_id" not in session or session.get("role") != "employer":
        return redirect("/login")
    return render_template('post_job.html')

@app.route('/post-job', methods=['POST'])
def post_job_submit():
    if "user_id" not in session or session.get("role") != "employer":
        return redirect("/login")

    title = request.form.get("title")
    details = request.form.get("details")
    stipend = request.form.get("stipend")
    location = request.form.get("location")

    if not title or not details or not stipend:
        flash("Please fill in all required fields.")
        return redirect("/post-job")

    with sqlite3.connect("your_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (employer_id, title, details, stipend, location)
            VALUES (?, ?, ?, ?, ?)
        """, (session["user_id"], title, details, stipend, location))
        conn.commit()

    flash("Job posted successfully!")
    return redirect("/dashboard")


@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")
@app.route("/help")
def help_page(): 
    return render_template("help.html")
@app.route("/forgetpass")
def forget_pass(): 
    return render_template("forgetpass.html")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route('/profile')
def profile():
    return render_template('profile.html')
@app.route('/hired')
def hired():
    return render_template('hired.html')

@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect("/login")  
    return render_template('dashboard.html') 

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
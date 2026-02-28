from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mess_secret_key"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS members(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                room TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS meals(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                date TEXT,
                breakfast INTEGER,
                veg INTEGER,
                nonveg INTEGER,
                night INTEGER,
                service INTEGER,
                total INTEGER)''')

    conn.commit()
    conn.close()

init_db()

# Create default admin
def create_admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username,password) VALUES (?,?)",("admin","admin"))
        conn.commit()
    conn.close()

create_admin()

# ---------- LOGIN ----------
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect('/dashboard')

    return render_template('login.html')

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM members")
    total_members = c.fetchone()[0]

    today = datetime.today().strftime('%Y-%m-%d')
    c.execute("SELECT SUM(total) FROM meals WHERE date=?", (today,))
    today_collection = c.fetchone()[0] or 0

    # Monthly data for chart
    current_month = datetime.today().strftime('%Y-%m')
    c.execute("""
        SELECT date, SUM(total)
        FROM meals
        WHERE date LIKE ?
        GROUP BY date
    """, (current_month + '%',))

    data = c.fetchall()

    dates = [row[0] for row in data]
    totals = [row[1] for row in data]

    conn.close()

    return render_template("dashboard.html",
                           total_members=total_members,
                           today_collection=today_collection,
                           dates=dates,
                           totals=totals)
# ---------- MEMBERS ----------
@app.route('/members', methods=['GET','POST'])
def members():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        room = request.form['room']
        c.execute("INSERT INTO members (name, room) VALUES (?,?)",(name,room))
        conn.commit()

    c.execute("SELECT * FROM members")
    data = c.fetchall()
    conn.close()

    return render_template("members.html", members=data)

# ---------- DAILY ENTRY ----------
@app.route('/daily', methods=['GET','POST'])
def daily():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM members")
    members = c.fetchall()

    if request.method == 'POST':
        member_id = request.form['member']
        breakfast = 20 if request.form.get('breakfast') else 0
        veg = 50 if request.form.get('veg') else 0
        nonveg = 90 if request.form.get('nonveg') else 0
        night = 30 if request.form.get('night') else 0

        service = 10 if (breakfast or veg or nonveg or night) else 0
        total = breakfast + veg + nonveg + night + service
        date = request.form['date']

        c.execute("""INSERT INTO meals
                     (member_id,date,breakfast,veg,nonveg,night,service,total)
                     VALUES (?,?,?,?,?,?,?,?)""",
                     (member_id,date,breakfast,veg,nonveg,night,service,total))
        conn.commit()

    conn.close()

    return render_template("daily.html", members=members)
# ---------- MONTHLY REPORT ----------
@app.route('/report')
def report():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    month = request.args.get('month')
    year = request.args.get('year')

    if not month or not year:
        month = datetime.today().strftime('%m')
        year = datetime.today().strftime('%Y')

    date_pattern = f"{year}-{month}-%"

    c.execute("""
        SELECT members.name, SUM(meals.total)
        FROM meals
        JOIN members ON meals.member_id = members.id
        WHERE meals.date LIKE ?
        GROUP BY members.name
    """, (date_pattern,))

    data = c.fetchall()

    c.execute("""
        SELECT SUM(total)
        FROM meals
        WHERE date LIKE ?
    """, (date_pattern,))

    monthly_total = c.fetchone()[0]
    if monthly_total is None:
        monthly_total = 0

    conn.close()

    return render_template("report.html",
                           data=data,
                           monthly_total=monthly_total,
                           month=month,
                           year=year)

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

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

# ---------- HOME ----------
@app.route('/')
def dashboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM members")
    total_members = c.fetchone()[0]

    today = datetime.today().strftime('%Y-%m-%d')

    c.execute("SELECT SUM(total) FROM meals WHERE date=?", (today,))
    today_collection = c.fetchone()[0]
    if today_collection is None:
        today_collection = 0

    conn.close()

    return f"""
    <h1>Mess Dashboard</h1>
    <h3>Total Members: {total_members}</h3>
    <h3>Today's Collection: ₹{today_collection}</h3>
    <a href='/members'>Manage Members</a><br>
    <a href='/daily'>Daily Entry</a>
    """

# ---------- ADD MEMBER ----------
@app.route('/members', methods=['GET','POST'])
def members():
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

    html = "<h2>Members</h2><form method='POST'>Name:<input name='name'> Room:<input name='room'><button>Add</button></form><hr>"
    for m in data:
        html += f"{m[1]} (Room {m[2]})<br>"

    html += "<br><a href='/'>Back</a>"
    return html

# ---------- DAILY ENTRY ----------
@app.route('/daily', methods=['GET','POST'])
def daily():
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

    html = "<h2>Daily Entry</h2><form method='POST'>"
    html += "Date:<input type='date' name='date'><br><br>"
    html += "Member:<select name='member'>"
    for m in members:
        html += f"<option value='{m[0]}'>{m[1]}</option>"
    html += "</select><br><br>"

    html += """
    Breakfast<input type='checkbox' name='breakfast'><br>
    Veg<input type='checkbox' name='veg'><br>
    NonVeg<input type='checkbox' name='nonveg'><br>
    Night<input type='checkbox' name='night'><br>
    <button>Submit</button></form>
    <br><a href='/'>Back</a>
    """
    return html

if __name__ == "__main__":
    app.run(debug=True)
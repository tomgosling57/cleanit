from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import os
from database import init_db, create_initial_owner

app = Flask(__name__)

# Create the 'instance' folder if it doesn't exist
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)

# Initialize the database and create an initial owner
Session = init_db(app)
create_initial_owner(Session)

# Dummy Data (will be replaced by database interactions)
DUMMY_USERS = {
    "cleaner1": {"id": "cleaner1", "name": "Alice", "role": "Cleaner"},
    "cleaner2": {"id": "cleaner2", "name": "Bob", "role": "Cleaner"},
    "cleaner3": {"id": "cleaner3", "name": "Charlie", "role": "Cleaner"},
    "teamleader1": {"id": "teamleader1", "name": "David", "role": "Team Leader"},
}

DUMMY_TEAMS = {
    "team_alpha": {"name": "Team Alpha", "cleaners": ["cleaner1", "cleaner2"]},
    "team_beta": {"name": "Team Beta", "cleaners": ["cleaner3"]},
}

DUMMY_BOOKINGS = [
    {
        "id": "job1",
        "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "time": "09:00",
        "duration": "2 hours",
        "assigned_cleaners": ["cleaner1", "cleaner2"],
        "team": "team_alpha",
        "job_title": "Office Cleaning - Downtown",
        "description": "Clean all offices, vacuum carpets, empty bins.",
        "report": ""
    },
    {
        "id": "job2",
        "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "time": "14:00",
        "duration": "3 hours",
        "assigned_cleaners": ["cleaner3"],
        "team": "team_beta",
        "job_title": "Residential Deep Clean - Suburbia",
        "description": "Deep clean kitchen and bathrooms, window cleaning.",
        "report": ""
    },
    {
        "id": "job3",
        "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "time": "10:00",
        "duration": "1 hour",
        "assigned_cleaners": ["cleaner1"],
        "team": "team_alpha",
        "job_title": "Retail Store Quick Clean",
        "description": "Sweep floors, dust shelves, clean front windows.",
        "report": ""
    },
    {
        "id": "job4",
        "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "time": "16:00",
        "duration": "2.5 hours",
        "assigned_cleaners": ["cleaner2", "cleaner3"],
        "team": "team_beta",
        "job_title": "Restaurant Kitchen Clean",
        "description": "Degrease kitchen, clean all surfaces, mop floors.",
        "report": ""
    },
    {
        "id": "job5",
        "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "time": "11:00",
        "duration": "4 hours",
        "assigned_cleaners": ["cleaner1", "cleaner3"],
        "team": "team_alpha",
        "job_title": "Warehouse Floor Scrub",
        "description": "Machine scrub warehouse floor, clear debris.",
        "report": ""
    },
]

CURRENT_USER = None # This will store the logged-in user's ID

@app.route('/')
def login():
    return render_template('login.html', users=DUMMY_USERS)

@app.route('/do_login', methods=['POST'])
def do_login():
    global CURRENT_USER
    user_id = request.form['user_id']
    if user_id in DUMMY_USERS:
        CURRENT_USER = user_id
        return redirect(url_for('timetable'))
    return redirect(url_for('login'))

@app.route('/timetable')
def timetable():
    if not CURRENT_USER:
        return redirect(url_for('login'))

    user = DUMMY_USERS[CURRENT_USER]
    user_role = user['role']
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user_role == "Cleaner":
        user_bookings = [
            booking for booking in DUMMY_BOOKINGS
            if CURRENT_USER in booking['assigned_cleaners']
        ]
        return render_template('index.html', user=user, bookings=user_bookings, today=today, users=DUMMY_USERS, teams=DUMMY_TEAMS)
    elif user_role == "Team Leader":
        # Group bookings by team for Team Leaders
        team_bookings = {team_id: [] for team_id in DUMMY_TEAMS}
        for booking in DUMMY_BOOKINGS:
            if booking['team'] in team_bookings:
                team_bookings[booking['team']].append(booking)
        return render_template('index.html', user=user, team_bookings=team_bookings, today=today, users=DUMMY_USERS, teams=DUMMY_TEAMS)
    
    return "Unauthorized", 403

@app.route('/job/<job_id>', methods=['GET', 'POST'])
def job_detail(job_id):
    if not CURRENT_USER:
        return redirect(url_for('login'))

    user = DUMMY_USERS[CURRENT_USER]
    user_role = user['role']
    
    job = next((b for b in DUMMY_BOOKINGS if b["id"] == job_id), None)
    if not job:
        return "Job not found", 404

    if request.method == 'POST' and user_role == "Team Leader":
        job['report'] = request.form['report']
        return redirect(url_for('timetable'))
    
    return render_template('job_cards.html', user=user, job=job, user_role=user_role, users=DUMMY_USERS, teams=DUMMY_TEAMS)

@app.route('/logout')
def logout():
    global CURRENT_USER
    CURRENT_USER = None
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
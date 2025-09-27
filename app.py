from flask import Flask, render_template, request, redirect, url_for, session
import os
from database import init_db, create_initial_owner
from routes.users import user_bp
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_bytes(32)

# Create the 'instance' folder if it doesn't exist
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)

# Initialize the database and create an initial owner
Session = init_db(app)
create_initial_owner(Session)
app.config['SQLALCHEMY_SESSION'] = Session

# Register blueprints
app.register_blueprint(user_bp)

@app.route('/')
def hello_world():
    return 'Hello, Flask!'

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# -- Init Stuff -- #
# Flask
app = Flask(__name__)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///airTrackerApp.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -- Models -- #
# Sensors
class tracker(db.Model):
    __tablename__ = "tracker"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class sensor(db.Model):
    __tablename__ = "sensor"
    id = db.Column(db.Integer, primary_key=True)
    trackerID = db.Column(db.Integer, db.ForeignKey("tracker.id"), nullable=False)
    sensorTypeID = db.Column(db.Integer, db.ForeignKey("sensorType.id"), nullable=False)
    sensorType = db.relationship("sensorType")

class sensorType(db.Model):
    __tablename__ = "sensorType"
    id = db.Column(db.Integer,primary_key=True)
    type = db.Column(db.String(50), unique=True, nullable=False)
    unit = db.Column(db.String(50), nullable=False)

# Data

# User

# -- Routes -- #
@app.route("/")
def index():
    return "Hello World"

# Dashboard
@app.route("/dashboard")
def dashboard():
    pass

# Analytics
@app.route("/analytics")
def analytics():
    pass

# Settings
@app.route("/settings")
def settings():
    pass

# Login Route
@app.route("/login")
def login():
    pass

# Logout Route
@app.route("/logout")
def logout():
    pass

# Register Route
@app.route("/register")
def register():
    pass

# -- Run Stuff -- #
if __name__ == "__main__":
    # Database
    with app.app_context():
        db.create_all()
    
    # Flask 
    app.run(debug=True)
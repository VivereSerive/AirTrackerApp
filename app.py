from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

# -- Init Stuff -- #
# Flask
app = Flask(__name__)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///airTrackerApp.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -- Functions -- #
def setUTC():
    return datetime.now(timezone.utc)

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
    tracker = db.relationship("tracker")

class sensorType(db.Model):
    __tablename__ = "sensorType"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), unique=True, nullable=False)
    unit = db.Column(db.String(50), nullable=False)

class status(db.Model):
    __tablename__ = "status"
    id = db.Column(db.Integer, primary_key=True)
    trackerID = db.Column(db.Integer, db.ForeignKey("tracker.id"), nullable=False)
    status = db.Column(db.String(50))
    lastConnected = db.Column(db.DateTime)
    tracker = db.relationship("tracker")

# Data
class data(db.Model):
    __tablename__ = "data"
    id = db.Column(db.Integer, primary_key=True)
    sensorID = db.Column(db.Integer, db.ForeignKey("sensor.id"), nullable=False)
    value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=setUTC, nullable=False)
    sensor = db.relationship("sensor")

class threshold(db.Model):
    __tablename__ = "threshold"
    id = db.Column(db.Integer, primary_key=True)
    sensorTypeID = db.Column(db.Integer, db.ForeignKey("sensorType.id"), nullable=False)
    warningVal = db.Column(db.Float)
    criticalVal = db.Column(db.Float)

class warning(db.Model):
    __tablename__ = "warning"
    id = db.Column(db.Integer, primary_key=True)
    dataID = db.Column(db.Integer, db.ForeignKey("data.id"), nullable=False)
    thresholdID = db.Column(db.Integer, db.ForeignKey("threshold.id"), nullable=False)
    alertedAt = db.Column(db.DateTime, default=setUTC, nullable=False)
    threshLevel = db.Column(db.String(50))
    data = db.relationship("data")
    threshold = db.relationship("threshold")

# User
class user(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)

class userTrackers(db.Model): # Trackers = Devices
    __tablename__ = "userTrackers"
    id = db.Column(db.Integer, primary_key=True)
    trackerID = db.Column(db.Integer, db.ForeignKey("tracker.id"), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tracker = db.relationship("tracker")
    user = db.relationship("user")

# -- Frontend Routes -- #
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

# -- Backend Routes -- #
@app.route("/data/POST", methods=["POST"])
def dataPOST():
    pass

@app.route("/data/WebSocket")
def dataWebSocket():
    pass

# -- Run Stuff -- #
if __name__ == "__main__":
    # Database
    with app.app_context():
        db.create_all()
    
    # Flask 
    app.run(debug=True)
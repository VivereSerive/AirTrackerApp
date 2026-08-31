from flask import Flask, session, render_template, url_for, flash, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_sock import Sock
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# -- Init -- #
# Flask
app = Flask(__name__)
sock = Sock()
app.config["SECRET_KEY"] = "airTrackerKEY1234"

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///airTrackerApp.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -- Global Variables -- #
PAYLOAD_KEY_TO_SENSOR_TYPE = {
    "co2Reading": "co2",
    "tempReading": "temperature",
    "humidityReading": "humidity",
    "pm25Reading": "pm25",
}

# -- Functions -- #
def setUTC():
    return datetime.now(timezone.utc)

@LoginManager.user_loader
def loadUser(userID):
    return user.query.get(int(userID))

def getUserTrackers():
    return(tracker.query.join(userTrackers).filter(userTrackers.userID == current_user.id).all())

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
    password = db.Column(db.String(255), nullable=False) # Updated to Store Hash
    email = db.Column(db.String(50), nullable=False)

    def writePass(self, rawPass):
        # Hash for Security
        self.password = generate_password_hash(rawPass)

    def checkPass(self, rawPass):
        return check_password_hash(self.password, rawPass)


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
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

# Dashboard
@app.route("/dashboard")
def dashboard():
    # -- Setup -- #
    trackers = getUserTrackers()
    latestStatus = {}
    latestData = {}

    # -- Get -- #
    # Tracker
    trackerIDs = [t.id for t in trackers]
    # Sensor
    sensors = sensor.query.filter(sensor.trackerID.in_(trackerIDs)).all()
    # Warnings
    activeWarnings = (warning.query.join(data).join(sensor)
                      .filter(sensor.trackerID.in_(trackerIDs))
                      .order_by(warning.alertedAt.desc())
                      .limit(10)
                      .all())

    # -- Process -- #
    for t in trackers:
        latestStatus[t.id] = (
            status.query.filter_by(trackerID=t.id)
            .order_by(status.lastConnected.desc())
            .first())
    for s in sensors:
        latestData[s.sensorType.type] = (
            data.query.filter_by(sensorID=s.id)
            .order_by(data.timestamp.desc())
            .first()
        )

    return render_template("dashboard.html", trackers=trackers, latestStatus=latestStatus, latestReadings=latestData, activeWarnings=activeWarnings)

# Analytics
@app.route("/analytics")
@login_required
def analytics():
    # -- Setup -- #
    trackers = getUserTrackers()
    readings = []

    # -- Get -- #
    # Tracker
    trackerIDs = [t.id for t in trackers]
    # Sensor
    sensors = sensor.query.filter(sensor.trackerID.in_(trackerIDs)).all()
    # User
    selectedSensorID = request.args.get("sensorID", type=int)
    days = request.args.get("days", default=7, type=int)

    # -- Process -- #
    if selectedSensorID:
        cutoff = db.func.datetime("now", f"-{days} days")
        readings = (
            data.query.filter(data.sensorID == selectedSensorID, data.timestamp >= cutoff)
            .order_by(data.timestamp.asc())
            .all()
        )

    # Chart.js
    chartLabels = [r.timestamp.strftime("%m/%d %H:%M") for r in readings]
    chartValues = [r.value for r in readings]

    return render_template(
        "analytics.html",
        sensors=sensors,
        selectedSensorID=selectedSensorID,
        days=days,
        chartLabels=chartLabels,
        chartValues=chartValues,
    )

# Settings
@app.route("/settings", methods=["POST", "GET"])
def settings():
    if request.method == "POST":
        for t in threshold.query.all():
            warningKey = f"warning-{t.id}"
            criticalKey = f"critical-{t.id}"
            if warningKey in request.form:
                t.warningVal = float(request.form[warningKey])
            if criticalKey in request.form:
                t.criticalVal = float(request.form[criticalKey])
        db.session.commit()
        flash("Settings saved")
        return redirect(url_for("settings"))

    thresholds = threshold.query.all()
    return render_template("settings.html", thresholds=thresholds)

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
    payload = request.get_json(silent=True)
    trackerDeviceID = payload.get("trackerID")
    trackerDevice = tracker.query.get(trackerDeviceID)

    # -- Verify -- #
    # Payload
    if payload is None:
        return jsonify({"error": "Not JSON"}), 400
    # Tracker ID
    if trackerDeviceID is None:
        return jsonify({"error": "Missing trackerID"}), 400
    # Tracker in Database
    if trackerDevice is None:
        return jsonify({"error": f"Tracker: {trackerDeviceID} not Found"}), 404

    # -- Process Data -- #
    createdRows = []

    # Loop through each possible reading type in the payload
    for payloadKey, sensorTypeName in PAYLOAD_KEY_TO_SENSOR_TYPE.items():
        if payloadKey not in payload:
            continue  # this reading wasn't included in this batch

        # Find the sensor on this tracker that matches this reading's type
        matchingSensor = (
            sensor.query.join(sensorType)
            .filter(sensor.trackerID == trackerDeviceID, sensorType.type == sensorTypeName)
            .first()
        )
        if matchingSensor is None:
            continue  # no sensor of this type exists for this tracker yet

        # Save the reading
        newData = data(sensorID=matchingSensor.id, value=float(payload[payloadKey]))
        db.session.add(newData)
        db.session.commit()  # commit now so newData.id is assigned

        # Check if this reading crosses a threshold, log a warning if so
        matchingThreshold = threshold.query.filter_by(sensorTypeID=matchingSensor.sensorTypeID).first()
        if matchingThreshold is not None:
            level = None
            if newData.value >= matchingThreshold.criticalVal:
                level = "critical"
            elif newData.value >= matchingThreshold.warningVal:
                level = "warning"

            if level:
                db.session.add(warning(dataID=newData.id, thresholdID=matchingThreshold.id, threshLevel=level))
                db.session.commit()

        createdRows.append({"sensorID": matchingSensor.id, "value": newData.value})

    return jsonify({"created": createdRows}), 201

@sock.route("/ws/tracker")
def trackerWS(ws):
    trackerDeviceID = request.args.get("trackerID", type=int)
    trackerDevice = tracker.query.get(trackerDeviceID)

    # Verifying Tracker 
    if trackerDeviceID is None:
        ws.close()
        return

    if trackerDevice is None:
        ws.close()
        return

    # Connect to Tracker
    db.session.add(status(trackerID=trackerDeviceID, status="online"))
    db.session.commit()

    # Connection Successful
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
    
    # Tracker Disconnects
    finally:
        db.session.add(status(trackerID=trackerDeviceID, status="offline"))
        db.session.commit()

# -- Run Stuff -- #
if __name__ == "__main__":
    # Database
    with app.app_context():
        db.create_all()
    
    # Flask 
    app.run(debug=True)
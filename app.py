from flask import Flask

# -- Init Stuff -- #
app = Flask(__name__)

# -- Models -- #


# -- Routes -- #
@app.route("/")
def index():
    pass

# Dashboard
@app.route("/dashboard")
def dashboard():
    pass

# Analytics
@app.route("/analytics")
def analytics():
    pass

# Settings
@app.settings("/settings")
def login():
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
    app.run(debug=True)
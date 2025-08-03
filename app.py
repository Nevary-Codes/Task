from flask import Flask, Response, render_template, redirect, url_for, request, jsonify, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from flask_bcrypt import Bcrypt
import bcrypt as bc
from bson import ObjectId
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import random
from bson.errors import InvalidId
import os
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "memorybox"

login_manager = LoginManager(app)
login_manager.init_app(app)
bcrypt = Bcrypt(app)



uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi("1"))
db = client["Task"]


class Admin(UserMixin):
    def __init__(self, admin_dict):
        self.id = str(admin_dict["_id"])
        self.email = admin_dict["email"]

@login_manager.user_loader
def load_user(user_id):
    admins = db["Admins"]
    admin = admins.find_one({"_id": ObjectId(user_id)})
    if admin:
        return Admin(admin)
    return None


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    return render_template("register.html")

from gridfs import GridFS

fs = GridFS(db)  # db is your MongoDB database instance

@app.route("/add_registration", methods=["POST"])
def registration():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    institution = request.form.get("institution")
    major = request.form.get("major")
    year = request.form.get("year")
    interests = request.form.get("interests")
    skills = request.form.get("skills")
    availability = request.form.get("availability")

    doc = {
        "name": name,
        "email": email,
        "phone": phone,
        "institution": institution,
        "major": major,
        "year": year,
        "interests": interests,
        "skills": skills,
        "availability": availability,
    }

    db["Registrations"].insert_one(doc)
    return redirect(url_for('home'))

@app.route("/admin")
@login_required
def admin():
    applicants = list(db.Registrations.find())
    print(applicants)
    return render_template("admin.html", applicants=applicants)

@app.route("/applicant")
@login_required
def applicant():
    aid = request.args.get("aid")
    applicant = list(db.Registrations.find({"_id": ObjectId(aid)}))

    return render_template("applicant.html", applicant=applicant[0])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("username")
        password = request.form.get("password")

        admin = db.Admins.find_one({"email": email})
        if admin and bc.checkpw(password.encode("utf-8"), admin["password"]):
            user = Admin(admin)
            login_user(user)
            return redirect(url_for("admin"))
        else:
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    with app.app_context():
        app.run(port=5000, debug=True)
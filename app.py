# login database connectivity
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from flask_mail import Mail , Message


# E- mail configuration


app = Flask(__name__)
app.secret_key = "supersecretkey"


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tiwariakarsh66@gmail.com'   # 👈 Your email
app.config['MAIL_PASSWORD'] = 'aoeb jytw lpqw wrbb'     # 👈 App Password (not normal password!)
app.config['MAIL_DEFAULT_SENDER'] = 'tiwariakarsh66@gmail.com'

mail = Mail(app)

# ---------- Database Config ----------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db) 

# ---------- Model ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(80), nullable = False)
    
# overall
class over(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=False)
    reason = db.Column(db.String(120), nullable=False)


# Create tables
with app.app_context():
    db.create_all()   



applications = []   


#pre loaded data
with app.app_context():
    db.create_all()

    # Preload HOD
    if not User.query.filter_by(username="hod123").first():
        hod = User(username="hod123", password="hodpass", role="hod")
        db.session.add(hod)

    # Preload Teacher
    if not User.query.filter_by(username="teacher123").first():
        teacher = User(username="teacher123", password="teacherpass", role="teacher")
        db.session.add(teacher)

    # Preload Guard
    if not User.query.filter_by(username="guard123").first():
        guard = User(username="guard123", password="guardpass", role="guard")
        db.session.add(guard)

    db.session.commit()

# ---------- Routes ----------
@app.route("/")
def home():
    if "username" in session:
        return render_template("gatepass.html")
    return render_template("login.html")

@app.route('/register_for')
def register_for():
    return render_template('register.html')


@app.route('/login_success')
def login_success():
    return render_template('gatepass.html')

@app.route('/register_success')
def register_success():
    return " registration successful"
@app.route('/del_success')
def del_success():
    return 'deletion successful'


@app.route("/users")
def users():
    all_users = User.query.all()  # fetch all rows
    return render_template("database.html", users=all_users)



@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        user = User.query.filter_by(username=username, password=password, role=role).first()

        if user:
            session["username"] = username
            session["role"] = role
            flash(f"Welcome, {username} ({role})!", "success")

            # Redirect based on role
            if role == "hod":
                return redirect(url_for("hod_dashboard"))
            elif role == "teacher":
                return redirect(url_for("teacher_dashboard"))
            elif role == "student":
                return redirect(url_for("login_success"))   # student gatepass page
            elif role == "guard":
                return redirect(url_for("success"))
        else:
            flash("Invalid credentials or role!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")
        
        if username and password and role:   # simpler check
            try:
                p = User(username=username, password=password, role=role)
                db.session.add(p)
                db.session.commit()
                flash("Registration successful!", "success")
                return redirect(url_for("login"))
            except IntegrityError:
                db.session.rollback()
                flash("Error: User already exists!", "danger")
                return redirect(url_for("register"))
        else:
            flash("All fields are required!", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Logged out successfully")
    return redirect(url_for("home"))

@app.route('/delete/<int:id>')
def erase(id): 
    data = User.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return redirect('/del_success')

# ---------- Gatepass Apply ----------
@app.route('/Apply', methods=['GET', 'POST'])
def Apply():
    if "username" not in session:
        flash("Login required!", "danger")
        return redirect(url_for("login"))

    name = request.form.get("Name")
    reason = request.form.get("Reason")

    if not name.strip():
        flash("Name cannot be empty!", "danger")
        return redirect(url_for('invalid'))
    if not reason.strip():
        flash("Reason is required!", "danger")
        return redirect(url_for('invalid'))
    
    all_app = over(username = name, reason = reason)
    db.session.add(all_app)
    db.session.commit()
    flash("added application in database successfully")

    applications.append({"id": len(applications) + 1, "name": name, "reason": reason, "status": "Pending"})
    flash(f"Gatepass request sent to HOD for approval, {name}!", "info")
    
    

    try:
        msg = Message(
            subject=" New gatepass request",
            recipients= ['hkup9973brahman@gmail.com'], # hod mail
            body= " dear message is sent to hod"
        )
        mail.send(msg)
    except Exception as e:
        return ' mail not sent to hod '

    return redirect(url_for('success'))    


@app.route('/success')
def success():
    return render_template("success.html", applications=applications)

@app.route('/invalid')
def invalid():
    return render_template("invalid.html")

# -------------------
# HOD Panel
# -------------------
@app.route('/hod')
def hod_dashboard():
    return render_template("hod_dashboard.html", applications=applications)

@app.route('/hod/approve/<int:app_id>')
def approve(app_id):
    for app_item in applications:
        if app_item["id"] == app_id:
            app_item["status"] = "Approved"
            flash(f"Application ID {app_id} approved!", "success")
            break
    return redirect(url_for('hod_dashboard'))

@app.route('/hod/reject/<int:app_id>')
def reject(app_id):
    for app_item in applications:
        if app_item["id"] == app_id:
            app_item["status"] = "Rejected"
            flash(f"Application ID {app_id} rejected!", "danger")
            break
    return redirect(url_for('hod_dashboard'))



# overall applicants database 
@app.route('/overall_app')
def overall_app():
    all_app = over.query.all()
    return render_template('overall_applicants.html' , overall_app = all_app)



if __name__ == "__main__":
    app.run( host = '0.0.0.0' ,debug=True)



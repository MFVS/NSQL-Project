from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, UserMixin, login_required
from wtforms import Form, StringField, PasswordField, validators

db = SQLAlchemy()
login_manager = LoginManager()

app = Flask(__name__)


# docker run --name kosmonauti -e POSTGRES_USER=Buzz -e POSTGRES_PASSWORD=Raketak -p 5432:5432 -d postgres
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://postgres:postgrespw@databasepg:5432'
app.config["SECRET_KEY"] = "secretkey"
db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

# Users


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)


with app.app_context():
    db.create_all()


class RegistrationForm(Form):
    username = StringField('Username: ', [validators.Length(min=4, max=15)])
    email = StringField("Email: ", [validators.Length(min=6, max=25)])
    password = PasswordField(
        "Password: ",
        [validators.DataRequired(), validators.EqualTo(
            "confirm", message='Passwords must match.')],
    )
    confirm = PasswordField("Confirm password: ")


class LoginForm(Form):
    username = StringField('Username: ', [validators.Length(min=4, max=15)])
    password = PasswordField('Password: ', [validators.DataRequired()])


@app.route('/', methods=['GET', 'POST'])
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        user = Users.query.filter_by(username=form.username.data).first()
        try:
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Check your username and password and try again.', 'error')
        except:
            flash('Check your username and password and try again.', 'error')
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        new_user = Users(
            username=form.username.data,
            password=form.password.data,
            email=form.email.data
        )
        try:
            db.session.add(new_user)
            db.session.commit()
        except:
            return "ERROR"
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form)


@app.route("/home")
@login_required
def home():
    return render_template("home.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/database")
@login_required
def database():
    users = Users.query.order_by(Users.id).all()
    return render_template("database.html", users=users)


if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0")

from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, UserMixin, login_required, current_user
from wtforms import Form, StringField, PasswordField, validators
from flask_mail import Mail, Message
import redis
from datetime import timedelta
from random import randint

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
r = redis.Redis(host = 'redis', port = 6379, decode_responses=True)


app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://postgres:postgrespw@databasepg:5432'
app.config["SECRET_KEY"] = "uhapw389a3ba30rai3b20sbj"
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'tm6990888@gmail.com'
app.config['MAIL_PASSWORD'] = 'cjjhivnvbzmyvlgk'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail.init_app(app)
db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

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
    confirm = PasswordField("Confirm password: ", [validators.Length(min=5, max=25)])

class LoginForm(Form):
    username = StringField('Username: ', [validators.Length(min=4, max=15)])
    password = PasswordField('Password: ', [validators.DataRequired()])

class AuthenticateForm(Form):
    password = PasswordField('Code: ', [validators.DataRequired()])


@app.route('/', methods=['GET', 'POST'])
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
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
            flash('ERROR','error')
            return render_template("register.html", form=form)
        heslo = randint(111,999)
        r.setex(f"{new_user.username}", timedelta(minutes=1), value = heslo)
        msg = Message('Authentication code.', sender = 'tm6990888@gmail.com', recipients = [f'{new_user.email}'])
        msg.body = f"{heslo}"
        mail.send(msg)
        session['new_user'] = new_user.id
        return redirect(url_for("authentication"))
    return render_template("register.html", form=form)

@app.route("/authentication", methods=["GET","POST"])
def authentication():
    form = AuthenticateForm(request.form)
    new_user = load_user(session.get('new_user'))
    if request.method == "POST" and form.validate():
        if form.password.data == r.get(new_user.username):
            login_user(new_user)
            return redirect(url_for("home"))
        else:
            flash('Wrong authentication code', 'error') 
    return render_template("authentication.html", form=form)

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

# @app.route('/user', methods = ['GET','PUT','DELETE'])
# def user_page():
#     return render_template('user.html')

if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0")

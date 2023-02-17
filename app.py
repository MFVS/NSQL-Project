from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, UserMixin, login_required, current_user
from wtforms import Form, StringField, PasswordField, validators, EmailField
from flask_mail import Mail, Message
import redis
from datetime import timedelta
from random import randint
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from neo4j import GraphDatabase
import neo_fs

# setup Mongo
MONGO_URI = "mongodb://user:password@mongo/test"
client = None
try:
    client = MongoClient(MONGO_URI)
    # client.admin.command('ping')
    print("MongoDB connected.")
except ConnectionFailure as e:
    print("MongoDB not available." + str(e))

# setup psql with sqlalchemy and mail
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
# setup Redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)

# setup Neo4j
# URI = "neo4j://localhost:7687"
# AUTH = ("neo4j", "test_heslo")
driver = GraphDatabase.driver("neo4j://neo4j:7687", auth=("neo4j", "test_heslo"))


app = Flask(__name__)

# App config
# hovn0vpacholiku@gmail.cz hovnovpacholiku
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://postgres:postgrespw@databasepg:5432'
app.config["SECRET_KEY"] = "uhapw389a3ba30rai3b20sbj"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'hovn0vpacholiku@gmail.com'
app.config['MAIL_PASSWORD'] = 'vtxctgxwwgcxfwpi'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail.init_app(app)
db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

# tabulka Users


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)


with app.app_context():
    db.create_all()


# Forms
class RegistrationForm(Form):
    username = StringField('Username: ', [validators.Length(min=4, max=15)])
    email = EmailField("Email: ", [validators.Length(min=6, max=25)])
    password = PasswordField(
        "Password: ",
        [validators.DataRequired(), validators.EqualTo(
            "confirm", message='Passwords must match.')],
    )
    confirm = PasswordField("Confirm password: ", [
                            validators.Length(min=5, max=25)])


class LoginForm(Form):
    username = StringField('Username: ', [validators.Length(min=4, max=15)])
    password = PasswordField('Password: ', [validators.DataRequired()])


class AuthenticateForm(Form):
    password = PasswordField('Code: ', [validators.DataRequired()])

# Routy
@app.route('/', methods=['GET', 'POST'])
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        user = Users.query.filter_by(username=form.username.data).first()
        try:
            if user.password == form.password.data:
                session['new_user'] = user.id
                return send()
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
            flash('ERROR', 'error')
            return render_template("register.html", form=form)    
        with driver.session() as neo:
            neo.execute_write(neo_fs.create_user, new_user.username)
        session['new_user'] = new_user.id
        return send()
    return render_template("register.html", form=form)


@app.route("/authentication", methods=["GET", "POST"])
def authentication():
    form = AuthenticateForm(request.form)
    new_user = load_user(session.get('new_user'))
    logout_user()
    if request.method == "POST" and form.validate():
        if form.password.data == r.get(new_user.username):
            login_user(new_user)
            return redirect(url_for("home"))
        else:
            flash('Wrong authentication code', 'error')
    return render_template("authentication.html", form=form)


@app.route('/friend_list', methods=['GET', 'POST'])
def friends():
    if request.method == 'POST':
        another_user = request.form['text']
        try:
            with driver.session() as neo:
                neo.execute_write(neo_fs.create_pending, current_user.username, another_user)
        except:
            flash('nejde to', 'error')
            return render_template('friend_list.html')
        return render_template('friend_list.html', another_user=another_user)
    with driver.session() as neo:
        pending = neo.execute_write(neo_fs.get_pending, current_user.username)
    with driver.session() as neo:
        friends = neo.execute_write(neo_fs.get_friends, current_user.username)
    return render_template('friend_list.html', pending = pending, friends = friends)


@app.route('/send_mail', methods=['GET'])
def send():
    user = load_user(session.get('new_user'))
    heslo = randint(100, 1000)
    r.setex(f"{user.username}", timedelta(minutes=1), value=heslo)
    msg = Message('Authentication code.',
                  sender='NosqlProject', recipients=[f'{user.email}'])
    msg.body = f"{heslo}"
    mail.send(msg)
    return redirect(url_for('authentication'))


@app.route('/chat')
def chat():
    with driver.session() as neo:
        friends = neo.execute_write(neo_fs.get_friends, current_user.username)
    return render_template('chat.html', friends=friends)


@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route('/accept_request/<friend>')
def accept(friend):
    with driver.session() as neo:
        neo.execute_write(neo_fs.create_friend, current_user.username, friend)
    return redirect(url_for('friends'))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/database")
@login_required
def database():
    users = Users.query.order_by(Users.id).all()
    return render_template("database.html", users=users)


@app.route('/favicon.ico')
def icon():
    return app.send_static_file('static/images/spaceship.png')


if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0")

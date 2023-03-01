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
MONGO_URI = "mongodb://user:password@mongo"
mongo_client = None
try:
    mongo_client = MongoClient(MONGO_URI)
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
neo_driver = GraphDatabase.driver("neo4j://neo4j:7687", auth=("neo4j", "test_heslo"))
neo_session = neo_driver.session()

app = Flask(__name__)

# App config
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://postgres:postgrespw@databasepg:5432'
app.config["SECRET_KEY"] = "uhapw389a3ba30rai3b20sbj"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'nevimkamo26@gmail.com'
app.config['MAIL_PASSWORD'] = 'Nevimkamo69'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
ALLOW_INVALID_HOST_MAIL = True
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
        neo_session.execute_write(neo_fs.create_user, new_user.username)
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
    pending = neo_session.execute_write(neo_fs.get_pending, current_user.username)
    friends = neo_session.execute_write(neo_fs.get_friends, current_user.username)
    outgoing = neo_session.execute_write(neo_fs.get_outgoing, current_user.username)
    if request.method == 'POST':
        # neo_session.execute_write(neo_fs.delete_all_duplicate_relationships)
        another_user = request.form['text']
        if another_user in [i.get('username') for i in friends]:
            return redirect(url_for('friends'))
        else:
            neo_session.execute_write(neo_fs.create_pending, current_user.username, another_user)
            return redirect(url_for('friends'))
    return render_template('friend_list.html', pending = pending, friends = friends, outgoing = outgoing)


@app.route('/send_mail', methods=['GET'])
def send():
    user = load_user(session.get('new_user'))
    heslo = r.execute_command('ACL GENPASS 9')
    r.setex(f"{user.username}", timedelta(minutes=1), value=heslo)
    msg = Message('Authentication code.',
                  sender='NosqlProject', recipients=[f'{user.email}'])
    msg.body = f"{heslo}"
    try:
        mail.send(msg)
    except Exception as e:
        if not ALLOW_INVALID_HOST_MAIL:
            raise e. with_traceback()
    return redirect(url_for('authentication'))


@app.route('/chat')
def chat():
    friends = neo_session.execute_write(neo_fs.get_friends, current_user.username)
    if len(friends) > 0:
        # redirects to chat with available friend if possible
        friend = friends.pop()
        return redirect("/chat/" "{}".format(friend.get("username")))
    default_messages = ["You have no friends yet :("]
    return render_template('chat.html', friends=friends, messages=default_messages)

# on click on friend-list in chatroom
@app.route('/chat/<username>', methods=['POST','GET'])
def chat_someone(username):
    assert(username and len(username)>0)
    if request.method == 'POST':
        message = request.form['textbox']
        if message == "":
            raise Exception("no message supplied, for now this is considered an error")
        entry = {"Sender":current_user.username, "Text":message}
        mongo_client["test"]["messages"].insert_one({"Sender":current_user.username, "Recipient":username, "Text":message})
        return redirect('/chat/{}'.format(username))
    friends = neo_session.execute_write(neo_fs.get_friends, current_user.username)
    condition = {"Sender":current_user.username, "Recipient":username}
    outgoing_messages = list(mongo_client["test"]["messages"].find(condition))
    condition = {"Sender":username, "Recipient":current_user.username}
    incoming_messages = list(mongo_client["test"]["messages"].find(condition))
    messages = [message.get("Sender") + "->" + str(message.get("Recipient"))+"\t"+message.get("Text") for message in incoming_messages + outgoing_messages]
    return render_template('chat.html', friends=friends, messages = messages)


@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route('/accept_request/<friend>')
def accept(friend):
    neo_session.execute_write(neo_fs.create_friend, current_user.username, friend)
    return redirect(url_for('friends'))

@app.route('/unfriend/<friend>')
def unfriend(friend):
    neo_session.execute_write(neo_fs.l_friend, current_user.username, friend)
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

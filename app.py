from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

app = Flask(__name__)                 #http://localhost:5000


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=True, nullable=False)

with app.app_context():
    db.create_all()


@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
      user = request.form['nm']
      password = request.form['pw']
      #email
      new_user = Users(username = user, password = password)

      try:
        db.session.add(new_user)
        db.session.commit()
        return redirect('/')
      except:
        return 'ERROR'

    else:
      users = Users.query.order_by(Users.id).all()
      return render_template('login.html', users = users)

@app.route('/register', methods = ['GET', 'POST'])
def register():
  return render_template('register.html')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/database')
def database():
  users = Users.query.order_by(Users.id).all()
  return render_template('database.html', users = users)

@app.route('/json')
def hello_js():
  return render_template('js.html')

if __name__== "__main__":
    app.run(debug=True, port = 5000)
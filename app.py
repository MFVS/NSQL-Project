from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

app = Flask(__name__)                 #http://localhost:5000
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=True, nullable=False)

with app.app_context():
    db.create_all()


@app.route('/', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
      user = request.form['nm']
      # password = request.form['pw']
      return render_template('home.html',name = user)
    else:
      user = request.args.get('nm')
      # password = request.args.get('pw')
      return render_template('login.html',name = user)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/number/<int:number>')
def hello_ok(number):
    return render_template('cislo.html', value = number)

@app.route('/json')
def hello_js():
  return render_template('js.html')

if __name__== "__main__":
    app.run(debug=True, port = 5000)
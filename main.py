from flask import Flask, render_template, request, session, url_for, flash, redirect
import bcrypt
from meal import get_req
from flask_sqlalchemy import SQLAlchemy
from waitress import serve
import requests

from werkzeug.security import generate_password_hash, check_password_hash

app= Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key='heudbw2735snd0182bdh376ch3865271'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self,email,password,name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self,password):
        return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

@app.route('/')
def dash():
    return render_template('dash.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')



    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/index')
        else:
            return render_template('login.html',error='Invalid user')

    return render_template('login.html')


@app.route('/index')
def index():
    session.clear()
    return render_template('index.html')


@app.route('/process_meal', methods=['GET', 'POST'])
def process_meal():
   
    if request.method == 'POST':
        meals = session.get('meals', {'breakfast': None, 'lunch': None, 'dinner': None})
        if 'breakfast' in request.form:
            breakfast= request.form.get('breakfast')
            meals['breakfast']=get_req(breakfast)
           
        elif 'lunch' in request.form:
            lunch= request.form.get('lunch')
            meals['lunch']=get_req(lunch)
            
        elif 'dinner' in request.form:
            dinner= request.form.get('dinner')
            meals['dinner']=get_req(dinner)
        session['meals']=meals    
        session.modified= True
        
    return render_template(
        "process_meal.html",
        bitems= meals['breakfast'],
        litems= meals['lunch'],
        ditems= meals['dinner']
        
  )
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug= True)
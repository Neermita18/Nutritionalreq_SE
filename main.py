from flask import Flask, render_template, request, session, url_for, flash, redirect
import bcrypt
import json
from meal import get_req
from flask_sqlalchemy import SQLAlchemy
from waitress import serve
import requests
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db,User, Meals, Details, Userdetails
import ast
from sqlalchemy import desc
from datetime import timedelta
from sqlalchemy import func
import pickle
import numpy as np
app= Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/91982/Desktop/SEPROJECT/instance/database.db'
db.init_app(app)
app.secret_key='heudbw2735snd0182bdh376ch3865271'


        	
with app.app_context():
    db.create_all()
with app.app_context():
    metadata = db.metadata
    
    # Get the specific table you want to drop from the metadata
    table_name = 'usersdb'
    table_to_drop = metadata.tables.get(table_name)
    
    # Drop the table if it exists
    if table_to_drop is not None:
        table_to_drop.drop(db.engine)
  

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
        session['name'] = name 
        new_user = User(name=name,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/succreglog')



    return render_template('register.html')

@app.route('/succreglog')
def succreglog():
    # Render registration success page
    return render_template('succreglog.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            session['name']=user.name
            
            return redirect('/index')
        else:
            return render_template('login_error.html')

    return render_template('login.html')

@app.route('/login_error')
def login_error():
    # Render login error page
    return render_template('login_error.html')

@app.route('/index')
def index():
    session.pop('meals', None)
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
         
        if all(meals.values()):
            
            # Store all meals in the database
            
           
            store_meal_in_database(meals)
            # flash('Meals information stored successfully!')
            # return redirect('/process_meal')  # Redirect to another page
        session['meals']=meals    
        session.modified= True
 
    return render_template(
        "process_meal.html",
        bitems= meals['breakfast'],
        litems= meals['lunch'],
        ditems= meals['dinner']
        
  )
def store_meal_in_database(meals):
    # Get the current date
    date = datetime.now().date()
    email = session.get('email')
    name = session.get('name')
    
    
    user_name = name
    # Get user_id from session, assuming it's stored there
    breakfast_json = json.dumps(meals['breakfast'])
    
    lunch_json = json.dumps(meals['lunch'])
    dinner_json = json.dumps(meals['dinner'])
    
    # Store the meal in the database
    new_meal =Meals(date=date,user_name=user_name, breakfast=breakfast_json, lunch=lunch_json, dinner=dinner_json)
    db.session.add(new_meal)
    db.session.commit()
    session.pop('meals', None)
    flash('Meals information stored successfully!')   
    
@app.route('/dashboard', methods=['GET','POST'])

def dashboard():
    user_name = session.get('name')    
    bmi=0
    user_details = db.session.query(Userdetails).filter_by(name=user_name).order_by(Userdetails.id.desc()).first()
    if user_details:
        age = user_details.age
        height= user_details.height
        h= user_details.height / 100  # Convert height to meters
        weight = user_details.weight
        gender = user_details.gender
        aclev= user_details.activity_level
        url = "https://fitness-calculator.p.rapidapi.com/dailycalorie"

        querystring = {"age":age,"gender":gender,"height":height,"weight":weight,"activitylevel":aclev}

        headers = {
                "X-RapidAPI-Key": "8bc4c7e788msh805f2fd04062842p14cac2jsnca0ad7e47526",
                "X-RapidAPI-Host": "fitness-calculator.p.rapidapi.com"
        }
        weights=[]
        response = requests.get(url, headers=headers, params=querystring)
        r= response.text
             
        datar= json.loads(r)
        bmr = datar['data']['BMR']
        
        maintain_weight_calories = datar['data']['goals']['maintain weight']
        mild_weight_loss_calories = datar['data']['goals']['Mild weight loss']['calory']
        weight_loss_calories = datar['data']['goals']['Weight loss']['calory']
        extreme_weight_loss_calories = datar['data']['goals']['Extreme weight loss']['calory']
        mild_weight_gain_calories = datar['data']['goals']['Mild weight gain']['calory']
        weight_gain_calories= datar['data']['goals']['Weight gain']['calory']
        extreme_weight_gain_calories = datar['data']['goals']['Extreme weight gain']['calory']
        # weight = [maintain_weight_calories, mild_weight_loss_calories, weight_loss_calories, extreme_weight_loss_calories, mild_weight_gain_calories, weight_gain_calories, extreme_weight_gain_calories]
        # weights.append(weight)
        weights.append({
                'maintain_weight_calories': maintain_weight_calories,
                'mild_weight_loss_calories': mild_weight_loss_calories,
                'weight_loss_calories': weight_loss_calories,
                'extreme_weight_loss_calories': extreme_weight_loss_calories,
                'mild_weight_gain_calories': mild_weight_gain_calories,
                'weight_gain_calories': weight_gain_calories,
                'extreme_weight_gain_calories': extreme_weight_gain_calories,
            })
        
        
        
        
        # Calculate BMI
        bmi = weight/pow(h,2)
        test=[[age, h, weight, bmi]]
        pickled_model = pickle.load(open('svm.pkl', 'rb'))
        predic=pickled_model.predict(test)
        predict=np.array_str(predic) 
        prediction= str(predict).replace('[','').replace(']','').replace('\'','').replace('\"','')
     
    else:
        bmi = "Want to know you BMI? Enter your details"
        prediction=None
        weights=None
    

          
    current_date = datetime.now().date()
    start_date = current_date - timedelta(days=7)
   
    # Query the database to get the last row for each date in the range
    last_meals = db.session.query(Meals.date, func.max(Meals.id)).\
                 filter(Meals.date >= start_date, Meals.date <= current_date, Meals.user_name == user_name).\
                 group_by(Meals.date).all()
                 
                 
   
    #print(last_meals)
    # Initialize a list to store the last meal for each date
    last_meals_data = []    
    for date, max_id in last_meals:
        meal = Meals.query.filter_by(date=date, id=max_id).first()
        #print(meal)
    
        bi= ast.literal_eval(meal.breakfast)
        li=ast.literal_eval(meal.lunch)
        di=ast.literal_eval(meal.dinner)
        # Loop through the fetched meals and print their attributes

        name= session.get('name')
        cal=0
        print(type(meal.date))
        for i in bi:
                cal+= i[1]
        for i in li:
                cal+=i[1]
        for i in di:
                cal+=i[1]
        print("Total Calories today: ",cal)
                
        fats=0

        for i in bi:
                fats+= i[2]
        for i in li:
                fats+=i[2]
        for i in di:
                fats+=i[2]
        print("Total Fats consumed today: ",fats, "g")

        proteins=0
        
        for i in bi:
                proteins+= i[3]
        for i in li:
                proteins+=i[3]
        for i in di:
                proteins+=i[3]
        print("Total Proteins consumed today: ",proteins, "g")
                
        total_carbs = 0
        total_carbs += sum(item[4] for item in bi)
        total_carbs += sum(item[4] for item in li)
        total_carbs += sum(item[4] for item in di)
        print("carbs: ",total_carbs )
                
        total_cholesterol = 0
        total_cholesterol += sum(item[5] for item in bi)
        total_cholesterol += sum(item[5] for item in li)
        total_cholesterol += sum(item[5] for item in di)
        print("cholesterol: ", total_cholesterol)
                
        sodium= 0
        sodium += sum(item[6] for item in bi)
        sodium += sum(item[6] for item in li)
        sodium+= sum(item[6] for item in di)
        print("sodium: ", sodium)
                
        potas=0
        potas += sum(item[7] for item in bi)
        potas+= sum(item[7] for item in li)
        potas += sum(item[7] for item in di)
        print("potassium: ", potas)
                
        sugar = 0
        sugar += sum(item[8] for item in bi)
        sugar+= sum(item[8] for item in li)
        sugar+= sum(item[8] for item in di)
        print("sugar: ", sugar)
        
        last_meals_data.append({
                'name': name,
                'date': date,
                'total_calories': cal,
                'total_proteins': proteins,
                'total_carbs': total_carbs,
                'total_fats': fats,
                'total_cholesterol': total_cholesterol,
                'total_sodium': sodium,
                'total_potassium': potas,
                'total_sugar': sugar
            })
        meals=[]
    for item in last_meals_data[::-1]:
        meals.append(item)
    if not meals:
        meals= None
        
    
    return render_template('dashboard.html', last_meals=meals, bmi=bmi, prediction=prediction, name= user_name, weights=weights)

@app.route('/data')
def data():
    return render_template('data.html')

@app.route('/submit', methods=['POST'])
def submit_data():
    if request.method == 'POST':
        age = request.form['age']
        height = request.form['height']
        weight = request.form['weight']
        gender = request.form['gender']
        activity_level = request.form['activity_level']

        # Check if the user exists in the details table
        name = session.get('name')
        existing_entry = Userdetails.query.filter_by(name=name).first()
        if existing_entry:
            # If the user exists, update the existing entry
            existing_entry.age = age
            existing_entry.height = height
            existing_entry.weight = weight
            existing_entry.gender = gender
            existing_entry.activity_level = activity_level
            # Update other fields similarly
        else:
            # If the user doesn't exist, create a new entry
            new_entry = Userdetails(name=name, age=age, height=height,weight=weight,gender=gender,activity_level=activity_level)
            # Add other fields similarly
            db.session.add(new_entry)

        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('dashboard.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug= True)
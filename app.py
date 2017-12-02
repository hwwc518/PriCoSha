from flask import Flask, flash, app, request, session, render_template, url_for,\
logging, redirect
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime, timedelta
import pymysql.cursors

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='password',
                       db='Pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


# timeout function
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)
    # if 'logged_in' not in session:
    #     flash('Timed out, please login again', 'danger')
    #     return redirect(url_for('login'))

@app.route('/')
def index():
    # if not session.get('logged_in'):
    #     return render_template('login.html')
    # else:
    return render_template('home.html')

class RegisterForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=50)])
    password = PasswordField('Password', [
            validators.DataRequired(),
            validators.EqualTo('confirm', message='Passwords do not match'),
            validators.Length(min=5, max=100)
        ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        username = form.username.data
        # Switch from sha to md5 b/c sha is too long
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = conn.cursor()
        
        # Check if Username already exists
        query = 'SELECT * FROM Person WHERE username = %s'
        cur.execute(query, (username))

        # Store query in variable
        data = cur.fetchone()

        # If user already exists
        if (data):
            # error = "This user already exists"
            flash('This username is already taken')
            cur.close()
            return redirect(url_for('register'))
            # return render_template('register.html', error=error)
        else:
            # Execute Query
            cur.execute("INSERT INTO Person(first_name, last_name, username, password)\
                    VALUES(%s, %s, %s, %s)", (first_name, last_name, username, password))

            # Commit to DB
            conn.commit()

            # Close the Connection
            cur.close()
            
            flash('You are now registered and can log in', 'success')

            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        # Get form fields 
        username = request.form['username']
        password_candidate = request.form['password']
       
        # Creating cursor
        cur = conn.cursor()

        # Get users from database
        query = cur.execute("SELECT * FROM Person WHERE username = %s", [username])

        # If you get a result from query
        if(query > 0):
            # get stored hashed password
            data = cur.fetchone()
            password = data['password']

            # Compare the passwords
            if sha256_crypt.verify(password_candidate, password):
                # Valid User
                session['logged_in'] = True
                session['username'] = username

                flash("You are now logged in", "success")
                return redirect(url_for("dashboard"))
            else:
                error = "Incorrect password"
                return render_template("login.html", error=error)
            
            # close connection
            cur.close()
        else:
            error = "Username not found" 
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check for if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Not authorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# search function
# add timeout session for extra feature
# Logout function
@app.route("/logout")
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Leads to dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT timest, content_name FROM Content WHERE username = %s ORDER BY\
    timest DESC'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('dashboard.html', username=username, posts=data)

@app.route('/post', methods=['GET', 'POST'])
def post():
     if 'logged_in' in session:
	username = session['username']
	cursor = conn.cursor();
	content_name = request.form['content_name']
	query = 'INSERT INTO Content (content_name, username) VALUES(%s, %s)'
	cursor.execute(query, (content_name, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('dashboard'))
     else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = "It's a secret to everybody"
    app.run(debug=True)




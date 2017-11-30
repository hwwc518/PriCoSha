from flask import Flask, flash, request, session, render_template, url_for,\
logging, redirect
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import datetime
import pymysql.cursors

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='password',
                       db='Pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

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

################# CONTENT FORM CLASS ##################
#content form should contain a body of content (data)
# class ContentForm(Form):
#     content = ContentField("Post something: ", validators=[DataRequired()])

#####################################################



############### MODEL STRUCTURE FOR CONTENT ###########
#create a class model for the content tailored to the user
#content should require timestamp,
#class Content(Model):
#    # username = ForeignKeyField(username, related_name= )
#    timestamp = DateTimeField(default=datetime.datetime.now)
#    #tagged =

#    body_content=Textfield()
#####################################################



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
        if ()
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

################### POSTING CONTENT ################
# @app.route('/post_content', methods = ('GET', 'POST'))
# def post_content():
#     form = forms.ContentForm()
#     if form.validate_on_submit():
#         flash('Content posted')
#         return redirect(url_for('index'))
#     return render_template('post_content.html', form=form)

#####################################################


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
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)




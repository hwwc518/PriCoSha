from flask import Flask, flash, request, session, render_template, url_for,\
logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
# import pymysql.cursors

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'passwd'
app.config['MYSQL_DB'] = 'Pricosha'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# initialize MySQL
mysql = MySQL(app)

# connection = pymysql.connect(host='localhost',
#                            user='user',
#                            password='passwd',
#                            db='db',
#                            charset='utf8mb4',
#                            cursorclass=pymysql.cursors.DictCursor)

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
            validators.Length(min=5, max=50)
        ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute Query
        cur.execute("INSERT INTO Person(first_name, last_name, username, password)\
                VALUES(%s, %s, %s, %s)", (first_name, last_name, username, password))

        # Commit to DB
        mysql.connection.commit()

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
        cur = mysql.connection.cursor()

        # Get users from database
        query = cur.execute("SELECT * FROM user WHERE username = %s", [username])

        # If you get a result from query
        if(query > 0):
            # get stored hashed password
            data = cur.fetchone()
            password = data['password']

            # Compare the passwords
            if sha256_crypt.verify(password, password_candidate):
                app.logger.info('PASSWORDS MATCH')
                # session['logged_in'] = True
            else:
                app.logger.info('PASSWORDS DO NOT MATCH')
        else:
            flash('Entered username/password DO NOT EXIST .__.')
            # return render_template('login.html')
            app.logger.info('NO USER')

    return render_template('login.html')

# @app.route("/logout")
# def logout():
#     session['logged_in'] = False
#     return index()

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)



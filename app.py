from flask import Flask, flash, app, request, session, render_template, url_for,\
logging, redirect
# from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime, timedelta
import pymysql.cursors

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='root',
                       port=8889,
                       db='pricosha1',
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
    return render_template('home.html')

# Leads to dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT timest, content_name, id FROM Content WHERE username = %s ORDER BY\
    timest DESC'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('dashboard.html', username=username, posts=data)


@app.route('/sendrequest', methods=['GET','POST'])
def send_friend_request():
    
    username = request.form['username']
    group_name = request.form['group_name']
    username_creator = request.form['username_creator']
    
    cur = conn.cursor()
    query = "SELECT * FROM Person WHERE username = %s && group_name = %s"
    cursor.execute(query, (username, group_name))
    data = cursor.fetchone()
    #error = None
    
    if (data):
        #error = "This friend is already in your friend group!"
        flash('This friend is already in your friend group!')
        return render_template('addfriend.html')
        #return render_template('addfriend.html', error = error)
    else:
        query = "INSERT INTO Person VALUES(%s, %s, %s)"
        cur.execute(query, (username, group_name, username_creator))
        conn.commit()
        cur.close()
        flash('Your friend {{username}} has been added to your friend group!')
        return render_template('addfriend.html')

@app.route('/addfriend', methods=['GET','POST'])
def addfriend():
    return render_template('addfriend.html')

@app.route('/post', methods=['GET', 'POST'])
def post():
    if 'logged_in' in session:
        #username
        username = session['username']
        cursor = conn.cursor()
        content_name = request.form['content_name']
        pub_status = True if request.form.get('public') else False

        query = 'INSERT INTO Content (content_name, username, public) VALUES(%s, %s, %s)'
        cursor.execute(query, (content_name, username, pub_status))
        conn.commit()
        cursor.close()


        return redirect(url_for('dashboard'))
    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))

#tag function
@app.route('/tag', methods=['GET' , 'POST'])
def tag():
    if 'logged_in' in session:
        #tagger is the user logged into the session
        tagger = session['username']
        taggee = request.form['taggee']
        contentID = request.form['contentID']
        print(request.form)

        #select content
        cur = conn.cursor()

        #Case 1: if user is self-tagging
        if taggee == tagger:
            status = 1
            print(contentID, tagger, taggee, status)
            query = cur.execute('INSERT INTO Tag (id, username_tagger, username_taggee, status)\
            VALUES(%s, %s, %s, %s)' , (contentID, tagger, taggee, status))

            flash('You have tagged yourself in this content!')
        #Case 2: is user is tagging someone else
        else:
            status = 0
            query = cur.execute('INSERT INTO Tag (id, username_tagger, username_taggee, status)\
            VALUES(%s, %s, %s, %s)',(contentID, tagger, taggee, status))

            flash('You have tagged ' + taggee + ' in this content!')
        conn.commit()
        cur.close()
        return redirect(url_for('dashboard'))

    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))

@app.route("/tags")
def tags():
    username = session['username']
    cur = conn.cursor()
    cur.execute('SELECT username_tagger, id FROM Tag WHERE username_taggee = %s AND status = 0', username)
    pendingTags = cur.fetchall()
    conn.commit()
    cur.close()
    return render_template("tags.html", pendingTags=pendingTags)

@app.route('/manageTags', methods=['GET', 'POST'])
def manageTags():
    taggee = session['username']
    tagger = request.form['tagger']
    id = request.form['id']
    approvalStatus = request.form['approval']
    cur = conn.cursor()
    
    if approvalStatus == "accept":
        cur.execute('UPDATE Tag SET status = 1 WHERE id = %s AND username_taggee = %s AND username_tagger = %s', (id, taggee, tagger))
        flash('The tag has been approved')
    else:
        cur.execute('DELETE FROM Tag WHERE id = %s AND username_taggee = %s AND username_tagger = %s', (id, taggee, tagger))
        flash('The tag has been deleted')

    cur.execute('SELECT username_tagger, id FROM Tag WHERE username_taggee = %s AND status = 0', taggee)
    pendingTags = cur.fetchall()

    conn.commit()
    cur.close()
    return render_template("tags.html", pendingTags=pendingTags)

@app.route('/creategroup')
def creategroup():
    return render_template('groups.html')

# Groups page - create and manage groups / friends
@app.route('/groups', methods=['GET','POST'])
def groups(): 
    if 'logged_in' in session:
        # check for create group action
        #if request.form['mems']:
        cursor = conn.cursor()
        creator = session['username']
        group_name = request.form['group_name']
        description = request.form['description']
        mems = request.form['mems']
        cursor = conn.cursor()
        
        query = 'INSERT INTO FriendGroup (group_name, username, description) VALUES(%s, %s, %s)'
        cursor.execute(query, (group_name, creator, description))
        
        listMems = mems.split(', ')
        
        #query2 = 'SELECT COUNT(*) FROM Member WHERE username = %s AND group_name = %s'

        
        #for all members in query
        invalidMems = []
        for mem in listMems:
            # verify if member is valid
            queryx = 'SELECT COUNT(*) FROM Person WHERE username = %s'
            if (cursor.execute(queryx, mem) == 1):
                query = 'INSERT INTO Member (username, group_name, username_creator) VALUES(%s, %s, %s)'
                cursor.execute(query, (mem, group_name, creator))
            else:
                invalidMems.append(mem)
    
        conn.commit()
        cursor.close()
        flash('The friend group has been successfully added!')
        return redirect(url_for('dashboard'))


#       mems = request.form['mems']
#       listMems = mems.split(', ')
# add creator first if not already in
#       query = 'SELECT COUNT(*) FROM Member WHERE username = %s AND group_name = %s'
# check logic / not sure if this works
#if (cursor.execute(query, (creator, group_name)) == 0):
#   query = 'INSERT INTO Member (username, group_name, username_creator)\VALUES(%s, %s, %s)'
#   query2 = 'INSERT INTO FriendGroup (group_name, username, description)\VALUES(%s, %s, %s)'
#   cursor.execute(query, (creator, group_name, creator))
#   cursor.execute(query2, (group_name, creator, description))
#   conn.commit()

# for all members in query
#       invalidMems = []
#       for mem in listMems:
#	        # verify if member is valid
#           queryx = 'SELECT COUNT(*) FROM Person WHERE username = %s'
#           if (cursor.execute(queryx, mem) == 1):
#               query = 'INSERT INTO Member (username, group_name, username_creator)\VALUES(%s, %s, %s)'
#               query2 = 'INSERT INTO FriendGroup (group_name, username, description)\VALUES(%s, %s, %s)'
#               cursor.execute(query, (mem, group_name, creator))
#               cursor.execute(query2, (group_name, mem, description))
#               conn.commit()
#           else:
#               invalidMems.append(mem)

# close connection
#   cursor.close()

# if there were invalid members, flash them and redirect
## todo: NOT DONE##
###################
###################
# if (invalidMems):
#     flash('')

#return render_template('home.html')
            # todo: add add member function
            ###############################
            ###############################
            
            
#            else:
#                flash('Timed out, please login again', 'danger')
#                #didn't work so replacing it temporarily
#                #return redirect(url_for('login'))
#                return render_template('home.html')



    else:
        flash('Timed out, please login again', 'danger')
        #didn't work so replacing it temporarily
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key = "It's a secret to everybody"
    app.run(debug=True)




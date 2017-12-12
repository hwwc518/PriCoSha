from flask import Flask, flash, app, request, session, render_template, url_for,\
logging, redirect
# from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime, timedelta
import pymysql.cursors

app = Flask(__name__)

#hoyin
# conn = pymysql.connect(host='localhost',
#                        user='root',
#                        password='root',
#                        port=8889,
#                        db='pricosha01',
#                        charset='utf8mb4',
#                        cursorclass=pymysql.cursors.DictCursor)

# ashley
# conn = pymysql.connect(host='localhost',
#                         user='root',
#                         password='root',
#                         port=8889,
#                         db='Pricosha',
#                         charset='utf8mb4',
#                         cursorclass=pymysql.cursors.DictCursor)

# hui
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
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
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
            cur.close()

    return render_template('login.html')

@app.route('/changePassword', methods=['POST','GET'])
def changePassword():
    if 'logged_in' in session:
        if request.method=='POST':
            # Create cursor
            cur = conn.cursor()

            curPass = request.form["currentPass"]
            password_cand = request.form["newPass"]
            password_cand = sha256_crypt.encrypt(str(password_cand))

            username = session['username']

            # Get users from database
            query = cur.execute('SELECT * FROM Person WHERE username = %s',\
                    [username])

            data = cur.fetchone()
            password = data['password']

            #Compare passwords
            if sha256_crypt.verify(curPass, password):
                # authorized to change pass
                cur.execute("UPDATE Person SET password=%s WHERE username=%s",\
                        (password_cand, username))
                
                # Commit to DB
                conn.commit()

                # Close Connection
                cur.close()

                session.clear();
                flash("Password changed successfully", "success")
                return redirect(url_for("login"))

            else:
                error = "Incorrect password"
                return render_template('changePassword.html', error=error)

    return render_template('changePassword.html')


@app.route('/changeUsername', methods=['POST','GET'])
def changeUsername():
    if 'logged_in' in session:
        if request.method=='POST':
            # Create cursor
            cur = conn.cursor()

            curPass = request.form["currPass"]
            username_cand = request.form["newUsername"]

            username = session['username']

            # Get users from database
            query = cur.execute('SELECT * FROM Person WHERE username = %s',\
                    [username])

            data = cur.fetchone()
            password = data['password']

            #Compare passwords
            if sha256_crypt.verify(curPass, password):
                # authorized to change pass
                cur.execute("UPDATE Person SET username=%s WHERE username=%s",\
                        (username_cand, username))
                
                # Commit to DB
                conn.commit()

                # Close Connection
                cur.close()

                session.clear()
                flash("Username changed successfully, please login again", "success")
                return redirect(url_for("login"))

            else:
                error = "Incorrect password"
                return render_template('changeUsername.html', error=error)

    return render_template('changeUsername.html')

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
    id DESC'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    
    query2= 'SELECT timest, comment_text, id, username FROM Comment WHERE username = %s ORDER BY id DESC'
    cursor.execute(query2, (username))
    comments = cursor.fetchall()
        
    query3 = 'SELECT Tag.timest, Tag.username_taggee, Tag.id, Person.first_name, Person.last_name FROM Tag NATURAL JOIN Person WHERE Tag.username_taggee = Person.username ORDER BY id DESC'
    cursor.execute(query3,)
    tags = cursor.fetchall()
    # cursor.close()
    
    #only the owner can share
    query4 = 'SELECT group_name FROM FriendGroup WHERE username = %s'
    cursor.execute(query4,(username))
    groups = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()

    tagged_query = 'SELECT DISTINCT Content.timest, content_name, Content.id \
    FROM Content JOIN Tag \
    ON Content.id = Tag.id \
    WHERE (username_taggee = %s) AND (status = 1) \
    ORDER BY timest DESC'
    cursor.execute(tagged_query,(username))
    data2 = cursor.fetchall()
    cursor.close()
    
    return render_template('dashboard.html', username=username, posts=data, comments=comments, tags = tags, taggedposts = data2)
    # return render_template('dashboard.html', username=username, posts=data,\
    #         comments=comments, tags = tags, groups = groups)
    
    #user can see all the posts that they made

@app.route('/addfriends', methods=['GET','POST'])
def add_friends():
    username = request.form['username']
    first_name = session["addfriend_first_name"]
    last_name = session["addfriend_last_name"]
    group_name = session["addfriend_group_name"]
    username_creator = session["addfriend_creator"]
    
    cur = conn.cursor()
    
    query2 = "SELECT * FROM Member WHERE username = %s && group_name = %s"
    cur.execute(query2, (username, group_name))
    data = cur.fetchone()
    
    if (data):
        flash('This friend is already in your friend group!', "danger")
        conn.commit()
        cur.close()
        return render_template('addfriend.html')
    else:
        query1 = "INSERT INTO Member(username, group_name, username_creator) VALUES(%s, %s, %s)"
        cur.execute(query1, (username, group_name, username_creator))
        conn.commit()
        cur.close()
        flash('Your friend has been added to your friend group!', "success")
        return render_template('addfriend.html')

@app.route('/addfriend', methods=['GET','POST'])
def add_friend():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    group_name = request.form['group_name']
    username_creator = request.form['username_creator']
    
    cur = conn.cursor()
    query1 = "SELECT COUNT(*) FROM Person WHERE first_name = %s && last_name = %s"
    cur.execute(query1, (first_name, last_name))
    num = cur.fetchone()
    
    if (num["COUNT(*)"]== 0):
        flash("This person does not exist! Tell them to create an account!", "danger")
        return render_template('addfriend.html')

    elif (num["COUNT(*)"] > 1):
        session["addfriend_first_name"] = first_name
        session["addfriend_last_name"] = last_name
        session["addfriend_group_name"] = group_name
        session["addfriend_creator"] = username_creator
        return render_template('altaddfriend.html')

    else:
        query2 = "SELECT username FROM Person WHERE first_name=%s && last_name=%s"
        cur.execute(query2, (first_name, last_name))
        username2 = cur.fetchone()
        
        query3 = "SELECT COUNT(*) FROM Member WHERE username = %s && group_name = %s"
        cur.execute(query3, (username2["username"], group_name))
        data = cur.fetchone()
        

        if (data["COUNT(*)"]!=0):
            flash('This friend is already in your friend group!', "danger")
            conn.commit()
            cur.close()
            return render_template('addfriend.html')
        else:
            query1 = "INSERT INTO Member(username, group_name, username_creator) VALUES(%s, %s, %s)"
            cur.execute(query1, (username2["username"], group_name, username_creator))
            conn.commit()
            cur.close()
            flash('Your friend has been added to your friend group!', "success")
            return render_template('addfriend.html')

@app.route('/deletefriend', methods=['GET','POST'])
def delete_friend():
    if (data):        
        query2 = "DELETE FROM Member WHERE username = %s && group_name = %s && username_creator = %s"
        cur.execute(query2, (username, group_name, username_creator))
        conn.commit()
        cur.close()
        flash('Your friend has been removed from your friend group!', "success")
        return render_template('addfriend.html')
    else:
        flash('This friend does not exist in your friend group!', "danger")
        return render_template('addfriend.html')

@app.route('/managefriend', methods=['GET','POST'])
def manage_friend():
    return render_template('addfriend.html')

@app.route('/post', methods=['GET', 'POST'])
def post():
    if 'logged_in' in session:
        #username
        username = session['username']
        cursor = conn.cursor()
        content_name = request.form['content_name']
        p_status = False if request.form.get('p_status') else True

        if p_status == True:
            query = 'INSERT INTO Content (content_name, username, public) VALUES(%s, %s, %s)'
            cursor.execute(query, (content_name, username, p_status))

            conn.commit()
            cursor.close()
            flash('You have successfully posted!', 'success')
            return redirect(url_for('dashboard'))

        elif p_status == False:
            query = 'INSERT INTO Content (content_name, username, public) VALUES(%s, %s, %s)'
            cursor.execute(query, (content_name, username, p_status))

            maxValQuery = 'SELECT MAX(id) FROM Content'
            cursor.execute(maxValQuery)
            maxVal = cursor.fetchone()
            maxVal = maxVal['MAX(id)']

            groupNames = request.form['groupNames']
            listOfGroupNames = groupNames.split(',')

            cursor = conn.cursor()
            for group in listOfGroupNames:
                query = 'INSERT INTO Share (id, group_name, username) VALUES (%s, %s, %s)'
                cursor.execute(query, (maxVal, group, username))
            conn.commit()
            cursor.close()
            flash('You have successfully posted to private group', 'success')
            return redirect(url_for('dashboard'))

    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))

@app.route('/sharepost', methods=['GET', 'POST'])
def sharepost():
    if 'logged_in' in session:
        username = session['username']
        contentID = request.form['contentID']
        group_name = request.form['group_name']

        cursor = conn.cursor()

        q1 = 'INSERT INTO Share(id, group_name, username) VALUES (%s, %s, %s)'
        cursor.execute(q1,(contentID, group_name, username))
        flash('You have successfully shared the post with your group!', 'success')
        conn.commit()
        cursor.close()
        return redirect(url_for('dashboard') )

    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))

#The user can only delete post that THEY themselves created
#Once the post is deleted, then all the tags and comments 
#related to that post is deleted along with the post itself
@app.route('/deletepost', methods=['GET', 'POST'])
def deletepost():
    if 'logged_in' in session:
        contentID = request.form['contentID']

        cur=conn.cursor()

        # delete all tags
        q1 = "DELETE FROM Tag WHERE id = %s"
        cur.execute(q1,(contentID))

        # delete all comments
        q2 = "DELETE FROM Comment WHERE id = %s"
        cur.execute(q2, (contentID))

        q4 = "DELETE FROM Share WHERE id = %s"
        cur.execute(q4,(contentID))

        # delete post
        q3 = "DELETE FROM Content WHERE id = %s"
        cur.execute(q3,(contentID))

        flash('You have deleted your post!', 'success')
        conn.commit()
        cur.close()
        return redirect(url_for('dashboard'))

    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))


@app.route('/comment', methods=['GET','POST'])
def comment():
    if 'logged_in' in session:
        username = session['username']
        commentID = request.form['commentID']
        comment_text = request.form['comment']

        cur = conn.cursor()
        query2 = 'INSERT INTO Comment (id, username, comment_text) VALUES(%s, %s, %s)'
        cur.execute(query2, (commentID, username, comment_text))
        flash('You have successfully added comment to this content!', 'success')

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

        #select content
        cur = conn.cursor()

        # check if user is valid
        # Get users from database
        query = cur.execute('SELECT * FROM Person WHERE username = %s',\
                [taggee])

        if (query > 0): 
            #Case 1: if user is self-tagging
            if taggee == tagger:
                status = 1
                print(contentID, tagger, taggee, status)
                query = cur.execute('INSERT INTO Tag (id, username_tagger, username_taggee, status)\
                VALUES(%s, %s, %s, %s)' , (contentID, tagger, taggee, status))

                flash('You have tagged yourself in this content!', 'success')
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
            flash("User does not exist", "danger")
            cur.close()
            return redirect(url_for("dashboard"))

    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))

#displays pending tags
@app.route("/tags")
def tags():
    if 'logged_in' in session:
        username = session['username']
        cur = conn.cursor()
        cur.execute('SELECT username_tagger, Content.id, content_name \
        FROM Tag JOIN Content\
        ON Content.id = Tag.id\
        WHERE username_taggee = %s AND status = 0', username)
        pendingTags = cur.fetchall()
        conn.commit()
        cur.close()

        return render_template("tags.html", pendingTags=pendingTags)
    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))

@app.route('/manageTags', methods=['GET', 'POST'])
def manageTags():
    if 'logged_in' in session:
        taggee = session['username']
        tagger = request.form['tagger']
        id = request.form['id']
        approvalStatus = request.form['approval']
        cur = conn.cursor()
        
        if approvalStatus == "accept":
            cur.execute('UPDATE Tag SET status = 1 WHERE id = %s AND username_taggee = %s AND username_tagger = %s', (id, taggee, tagger))
            flash('The tag has been approved', 'success')
        else:
            cur.execute('DELETE FROM Tag WHERE id = %s AND username_taggee = %s AND username_tagger = %s', (id, taggee, tagger))
            flash('The tag has been deleted', 'success')

        cur.execute('SELECT username_tagger, id FROM Tag WHERE username_taggee = %s AND status = 0', taggee)
        pendingTags = cur.fetchall()

        conn.commit()
        cur.close()
        return render_template("tags.html", pendingTags=pendingTags)
    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))


@app.route('/creategroup')
def creategroup():
    return render_template('groups.html')

@app.route('/deletegroups', methods=['GET', 'POST'])
def delete_group():
    if 'logged_in' in session:
        # check for create group action
        #if request.form['mems']:
        cursor = conn.cursor()
        username = session['username']
        group_name = request.form['group_name']
        cursor = conn.cursor()
        
        query1 = 'SELECT * FROM FriendGroup WHERE username = %s AND group_name = %s'
        query2 = 'SELECT username FROM FriendGroup WHERE group_name = %s'
        cursor.execute(query2, group_name)
        data = cursor.fetchone()
        #check if the group exists
        if (cursor.execute(query1, (username, group_name)) == 0):
            print("Inside if")
            flash("The group doesn't exist!", "danger")
            conn.commit()
            return redirect(url_for('creategroup'))
        #check if the user is the creator... only giving creator the permission to delete the group
        elif (data["username"] != username):
            print("Inside elif")
            flash("You do not have the permission to delete this group!", "danger")
            conn.commit()
            return redirect(url_for('creategroup'))
        
        else:
            print("Inside else")
            query3 = 'SELECT * FROM Member WHERE group_name = %s'
            cursor.execute(query3, group_name)
            data2 = cursor.fetchall()
            
            #delete all members
            for mem in data2:
                mem_username = mem["username"]
                query4 = 'DELETE from Member WHERE username = %s AND group_name = %s'
                cursor.execute(query4, (mem_username, group_name))
        
            #delete member group
            query5 = 'DELETE from FriendGroup WHERE group_name = %s AND username = %s'
            cursor.execute(query5, (group_name, username))
            
            conn.commit()
            cursor.close()
            
            flash("Your friend group was successfully deleted!", "success")
            return redirect(url_for('dashboard'))
    
    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))


# Groups page - create and manage groups / friends
@app.route('/addgroups', methods=['GET','POST'])
def add_groups():
    if 'logged_in' in session:
        # check for create group action
        #if request.form['mems']:
        cursor = conn.cursor()
        creator = session['username']
        group_name = request.form['group_name']
        description = request.form['description']
        mems = request.form['mems']
        cursor = conn.cursor()
        
        query1 = 'SELECT COUNT(*) FROM Member WHERE username = %s AND group_name = %s'
        if (cursor.execute(query1, (creator, group_name)) == 0):
           query2 = 'INSERT INTO Member (username, group_name, username_creator)\VALUES(%s, %s, %s)'
           query3 = 'INSERT INTO FriendGroup (group_name, username, description)\VALUES(%s, %s, %s)'
           cursor.execute(query2, (creator, group_name, creator))
           cursor.execute(query3, (group_name, creator, description))
           conn.commit()
        
        query4 = 'INSERT INTO FriendGroup (group_name, username, description) VALUES(%s, %s, %s)'
        cursor.execute(query4, (group_name, creator, description))
        
        listMems = mems.split(', ')
        
        #for all members in query
        invalidMems = []
        for mem in listMems:
            # verify if member is valid
            print(mem)
            query5 = 'SELECT * FROM Person WHERE username = %s'
            val = cursor.execute(query5, mem)
            print(val)
            if (val == 1):
                query6 = 'INSERT INTO Member (username, group_name, username_creator) VALUES(%s, %s, %s)'
                cursor.execute(query6, (mem, group_name, creator))
            else:
                invalidMems.append(mem)
    
        conn.commit()
        cursor.close()
        
        if (len(invalidMems)!= 0):
            error = "Following friends could not be added: "
            for mem in invalidMems:
                error = error + str(mem) + " "
            flash(error, "danger")
        else:
            flash('The friend group has been successfully added!', "success")

        return redirect(url_for('dashboard'))
            
    else:
        flash('Timed out, please login again', 'danger')
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key = "It's a secret to everybody"
    app.run(debug=True)

from flask import Flask, flash, request, session, render_template
import pymysql.cursors

app = Flask(__name__)

connection = pymysql.connect(host='localhost',
                           user='user',
                           password='passwd',
                           db='db',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('home.html')

@app.route('/login', methods=['POST','GET'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    with connection.cursor() as cursor:
        sql = "SELECT * FROM user WHERE username = %s and password = %s"
        cursor.execute(sql, (username, password))
        result = cursor.fetchone()
        print(result)
    connection.commit()

    if(result):
        if username == result[username] and password == result[password]:
        session['logged_in'] = True
    else:
        flash('Entered username/password DO NOT EXIST .__.')
        return render_template('login.html')

    return index()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return index()

if __name__ == '__main__':
    app.run(debug=True)



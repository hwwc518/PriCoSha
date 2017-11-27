from flask import Flask, flash, request, session, render_template

app = Flask(__name__)

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('home.html')
@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == 'user' and request.form['password'] == 'password':
        session['logged_in'] = True
    else:
        flash('password DOES NOT EXIST .__.')
    return index()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return index()

if __name__ == '__main__':
    app.run(debug=True)



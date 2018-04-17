from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import datetime

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'kalender_app'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# Init MySQL
mysql = MySQL(app)

# Index
@app.route('/')
def home():
    now = datetime.datetime.now()
    return render_template('index.html', now=now)

# Register form class - using WTForms
class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=6, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match!')
    ])
    confirm = PasswordField('Confirm Password')

# Register - still need to check unique username...
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create a cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute('INSERT INTO users(username, email, password) VALUES(%s, %s, %s)', [username, email, password])

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered. Proceed to login.', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute('SELECT * FROM users WHERE username = %s', [username])


        if result > 0:
            # Username found

            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare candidate and stored hash
            if sha256_crypt.verify(password_candidate, password):

                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('home'))
            else:

                # Did not pass
                error = 'Invalid login'
                return render_template('login.html', error=error)

            # Close connection
            cur.close()
        else:

            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user is logged in
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised page, please log in.', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Successfully logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = 'secret'
    app.run(debug=True)

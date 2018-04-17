from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import datetime, calendar

app = Flask(__name__)


# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'kalender_app'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# Init MySQL
mysql = MySQL(app)

def month_name(month_number):
    if month_number == 1:
        return 'January'
    elif month_number == 2:
        return 'February'
    elif month_number == 3:
        return 'March'
    elif month_number == 4:
        return 'April'
    elif month_number == 5:
        return 'May'
    elif month_number == 6:
        return 'June'
    elif month_number == 7:
        return 'July'
    elif month_number == 8:
        return 'August'
    elif month_number == 9:
        return 'September'
    elif month_number == 10:
        return 'October'
    elif month_number == 11:
        return 'November'
    elif month_number == 12:
        return 'December'

# Index
@app.route('/')
def home():
    # Determine current date
    now = datetime.datetime.now()

    # Set current month and year default for now
    current_month = now.month
    current_year = now.year

    # Create data to populate calendar
    cal_month = calendar.monthcalendar(current_year, current_month)

    # Create data from a month before
    if current_month == 1:
        cal_month_prev = calendar.monthcalendar(current_year - 1, 12)
    else:
        cal_month_prev = calendar.monthcalendar(current_year, current_month - 1)

    # Create data for the next month
    if current_month == 12:
        cal_month_next = calendar.monthcalendar(current_year + 1, 1)
    else:
        cal_month_next = calendar.monthcalendar(current_year, current_month + 1)

    # String for months: prev, current, after
    month_name_prev = month_name(current_month - 1)
    month_name_current = month_name(current_month)
    month_name_next = month_name(current_month + 1)

    return render_template('index.html', now=now,
        cal_month=cal_month, cal_month_prev=cal_month_prev, cal_month_next=cal_month_next,
        month_name_prev=month_name_prev, month_name_current=month_name_current, month_name_next=month_name_next)

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

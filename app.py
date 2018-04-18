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

# Define names for the months of the year
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
    return make_calendar(now.month, now.year)

# Make calendar months
@app.route('/<int:month>_<int:year>')
def make_calendar(month, year):
    # Determine current date
    now = datetime.datetime.now()
    now_month_name = month_name(now.month)

    # Set current month and year
    current_month = month
    current_year = year

    # Create data to populate calendar
    cal_month = calendar.monthcalendar(current_year, current_month)
    month_name_current = month_name(current_month)

    # Create data from a month before
    if current_month == 1:
        cal_month_prev = calendar.monthcalendar(current_year - 1, 12)
        month_prev = 12
        month_name_prev = month_name(month_prev)
    else:
        cal_month_prev = calendar.monthcalendar(current_year, current_month - 1)
        month_prev = current_month - 1
        month_name_prev = month_name(month_prev)

    # Create data for the next month
    if current_month == 12:
        cal_month_next = calendar.monthcalendar(current_year + 1, 1)
        month_next = 1
        month_name_next = month_name(month_next)
    else:
        cal_month_next = calendar.monthcalendar(current_year, current_month + 1)
        month_next = current_month + 1
        month_name_next = month_name(month_next)

    # Add dates from previous month to blank spaces
    for i in range(7):
        if cal_month[0][i] == 0:
            cal_month[0][i] = 32 * cal_month_prev[(len(cal_month_prev)-1)][i]

    # Add dates from next month to blank spaces
    for i in range(7):
        if cal_month[(len(cal_month)-1)][i] == 0:
            cal_month[(len(cal_month)-1)][i] = 32 * cal_month_next[0][i]

    notes = []
    if ('logged_in' in session):
        # POPULATE CALENDAR WITH SAVED NOTE TITLES

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute('SELECT * FROM notes WHERE username=%s AND date_month=%s AND date_year=%s', (session['username'], current_month, current_year))

        notes = cur.fetchall()

    return render_template('index.html', notes=notes, now=now, now_month_name=now_month_name, month_prev=month_prev, month_next=month_next, current_month=current_month, current_year=current_year,
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
            flash('You must be logged in to access this page.', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Successfully logged out.', 'success')
    return redirect(url_for('home'))

# Individual date's notes
@app.route('/<int:year>-<int:month>-<int:day>')
@login_required
def date(year, month, day):
    # Display the string name for the chosen date
    selected_month_name = month_name(month)

    # Create cursor
    cur = mysql.connection.cursor()

    # Get notes for selected date and user
    result = cur.execute("SELECT * FROM notes WHERE username=%s AND date_day=%s AND date_month=%s AND date_year=%s", (session['username'], day, month, year))

    notes = cur.fetchall()

    if result > 0:
        return render_template('date.html', notes=notes,
            year=year, month=month, selected_month_name=selected_month_name, day=day)
    else:
        error = "No notes for selected date"
        return render_template('date.html', error=error,
            year=year, month=month, selected_month_name=selected_month_name, day=day)

    # Close connection
    cur.close()

# Note form class
class NoteForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=60)])
    body = TextAreaField('Body')

# Create a note for a particular date
@app.route('/create-note_<int:year>-<int:month>-<int:day>', methods=['GET', 'POST'])
@login_required
def create_note(year, month, day):
    selected_month_name = month_name(month)
    form = NoteForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute db
        cur.execute("INSERT INTO notes(username, title, body, date_day, date_month, date_year) VALUES(%s, %s, %s, %s, %s, %s);", (session['username'], title, body, day, month, year))

        # Commit to db
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Note created', 'success')
        return date(year, month, day)

    return render_template('create-note.html', form=form, year=year, month=month, selected_month_name=selected_month_name, day=day)

# Update a note for a particular date
@app.route('/edit-note_<string:id>', methods=['GET', 'POST'])
@login_required
def edit_note(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by ID and username
    result = cur.execute("SELECT * FROM notes WHERE id=%s AND username=%s", [id, session['username']])

    note = cur.fetchone()

    # Details to use on the page
    year = note['date_year']
    month = note['date_month']
    day = note['date_day']
    selected_month_name = month_name(month)

    # Get form
    form = NoteForm(request.form)

    # Populate note form fields
    form.title.data = note['title']
    form.body.data = note['body']

    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute db
        cur.execute("UPDATE notes SET title=%s, body=%s WHERE id=%s AND username=%s);", (title, body, id, session['username']))

        # Commit to db
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Note updated', 'success')
        return date(year, month, day)

    return render_template('create-note.html', form=form)

    return render_template('create-note.html', form=form, year=year, month=month, selected_month_name=selected_month_name, day=day)

# Delete a particular note
@app.route('/delete-note_<string:id>')
@login_required
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute - retrieve information for return journey
    cur.execute('SELECT * FROM notes WHERE id=%s AND username=%s', [id, session['username']])

    note = cur.fetchone()

    year = note['date_year']
    month = note['date_month']
    day = note['date_day']

    # Execute - remove from db
    cur.execute('DELETE FROM notes WHERE id=%s AND username=%s', [id, session['username']])

    # Commit to db
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('Note deleted', 'success')
    return date(year, month, day)

if __name__ == '__main__':
    app.secret_key = 'secret'
    app.run(debug=True)

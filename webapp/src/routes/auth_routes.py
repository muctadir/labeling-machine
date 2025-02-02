from flask import request, redirect, url_for, flash
from flask_login import login_user, logout_user
from sqlalchemy import select
from werkzeug.security import check_password_hash

from src import app, db
from src.database.models import User
from src.helper.tools_common import string_none_or_empty


@app.route("/signin", methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        if string_none_or_empty(request.form['user']) or string_none_or_empty(request.form['password']):
            return redirect(url_for('index'))

        username = request.form['user'].strip()
        password = request.form['password']
        user = db.session.execute(select(User).where(User.username == username)).scalar()
        if user is not None and check_password_hash(user.password, password):
            login_user(user, force=True)
        else:
            flash('Authentication failed!!!', category='error')

        return redirect(url_for('index'))
    else:
        return "Not POST!"


# Todo: signup currently disabled
# @app.route("/signup", methods=['GET', 'POST'])
# def signup():
#     if request.method == 'GET':
#         if 'new_user_username' not in session:
#             # Try to log-in from home
#             return redirect(url_for('index'))
#         else:
#             tmp = session['new_user_username']  # Passed username from home page
#             session.pop('new_user_username', None)
#             return render_template('common_pages/signup.html', username=tmp)
#     else:
#         username = request.form['name']
#         gender = request.form['gender']
#         education = request.form['education']
#         occupation = request.form['occupation']
#         affiliation = request.form['affiliation']
#         xp = request.form['years_xp']
#         user_item = User(username=username, gender=gender, education=education, occupation=occupation,
#                          affiliation=affiliation, years_xp=xp)
#         db.session.add(user_item)
#         db.session.commit()
#         sign_in(username)
#         return redirect(url_for('index'))


@app.route("/signout", methods=['GET', 'POST'])
def signout():
    if request.method == 'GET':
        logout_user()
        return redirect(url_for('index'))
    else:
        return "Not GET!"

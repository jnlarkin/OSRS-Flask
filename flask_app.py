from flask import Flask, request, render_template, url_for, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "123412hkasdjkas"

db = SQLAlchemy(app)


class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(100))

    def __init__(self, name, password):
        self.name = name
        self.password = password
        pass

@app.route("/")
def hello_world():
    return render_template('base.html')


@app.route("/user/<username>", methods=['POST', 'GET'])
def return_user(username):
    email = None
    if 'user' in session:
        if request.method == "POST":
            email = request.form["email"]
            session['email'] = email
            session_name = session['user']
            found_name = users.query.filter_by(name=session_name).first()
        return render_template('user.html', user=username, email=None)


    else:
        return redirect(url_for('login'))

@app.route('/signup', methods = ['POST', 'GET'])
def signup():
    if request.method == 'POST':
        form_user = request.form['username']
        form_password = request.form['password']

        if form_user and form_password != '' or None:
            add_usr = users(form_user, form_password)
            db.session.add(add_usr)
            db.session.commit()
            session['user'] = form_user
            return redirect(url_for('return_user', username=session['user']))
        else:
            print("please enter user and password")
            return redirect(url_for('signup'))
    else:
        return render_template('signup.html')


@app.route("/login", methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':

        form_user = request.form['username']
        form_password = request.form['password']

        if form_user and form_password != '' or None:
            found_user = users.query.filter_by(name=form_user).first()
            if found_user:
                if found_user.password == form_password:
                    session['user'] = found_user.name
                    return redirect(url_for('return_user', username=session['user']))
                else:
                    error = "Wrong username or password"
                    flash('Wrong username or password', 'errors')
                    print("wrong username or password")
                    return render_template('login.html', error=error)
            else:
                error = "Wrong username or password"
                flash('Wrong username or password', 'errors')
                print("wrong username or password")
                return render_template('login.html', error=error)
        else:
            print("please enter user and password")
            return redirect(url_for('login'))



        # session['user'] = form_user
        # session['email'] = form_email
        # user = session['user']
        # email = session['email']
        # found_user = users.query.filter_by(name=user).first()
        # if found_user and found_user.email:
        #     session['user'] = found_user
        #     session['email'] = found_user.email
        #     return redirect(f'/user/{session["user"]}')
        # if found_user:
        #     session['user'] = found_user
        #     return redirect(f'/user/{session["user"]}')
        # else:
        #     if email:
        #         add_usr = users(user, email)
        #         db.session.add(add_usr)
        #         db.session.commit()
        #         return redirect(f'/user/{user}')
        #     else:
        #         add_usr = users(user, '')
        #         db.session.add(add_usr)
        #         db.session.commit()
        #         return redirect(f'/user/{user}')


    elif 'user' in session:
        return redirect(url_for('return_user', username=session['user']))
    else:
        return render_template('login.html')


@app.route("/logout")
def logout():
    session.pop('user', None)
    flash('Logged out Successfully', 'successes')
    return redirect(url_for('login'))


@app.route("/items")
def return_items():
    return render_template('items.html')


@app.route("/database")
def view_db():
    return render_template('view_db.html', values=users.query.all())

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

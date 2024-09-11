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
    email = db.Column(db.String(100))

    def __init__(self, name, email):
        self.name = name
        self.email = email
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
            found_email = users.query.filter_by(email=email).first()
            if found_email:
                pass
            else:
                pass
                # add_usr = users(found_name, email)
                # db.session.add(add_usr)
                # db.session.commit()


        elif 'email' in session['email']:
            email = session['email']

        return render_template('user.html', user=username, email=session['email'])
    else:
        return redirect(url_for('login'))


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        form_user = request.form['nm']
        form_email = request.form['email']
        session['user'] = form_user
        session['email'] = form_email
        user = session['user']
        email = session['email']
        found_user = users.query.filter_by(name=user).first()
        found_email = users.query.filter_by(email=email).first()
        if found_user and found_email:
            session['user'] = found_user
            session['email'] = found_email
        else:
            add_usr = users(user, email)
            db.session.add(add_usr)
            db.session.commit()

        return redirect(f'/user/{user}')
    elif 'user' in session:
        return redirect(url_for('return_user', username=session['user']))
    else:
        return render_template('login.html')


@app.route("/logout")
def logout():
    session.pop('user', None)
    session.pop('email', None)
    flash('Logged out Successfully', 'info')
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

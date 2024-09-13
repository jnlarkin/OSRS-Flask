from flask import Flask, request, render_template, url_for, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import requests
import json

app = Flask(__name__)
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "123412hkasdjkas"

db = SQLAlchemy(app)

scheduler = BackgroundScheduler()



class Users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(100))

    def __init__(self, name, password):
        self.name = name
        self.password = password

class Items(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    buy_limit = db.Column(db.Integer)
    high_alchemy = db.Column(db.Integer)
    high = db.Column(db.Integer)
    low = db.Column(db.Integer)
    margin = db.Column(db.Integer)

    def __init__(self, id, name, buy_limit, high_alchemy, high, low, margin):
        self.id = id
        self.name = name
        self.buy_limit = buy_limit
        self.high_alchemy = high_alchemy
        self.high = high
        self.low = low
        self.margin = margin

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'buy_limit': self.buy_limit,
            'high_alchemy': self.high_alchemy,
            'high': self.high,
            'low': self.low,
            'margin': self.margin
        }

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    high = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, item_id, high):
        self.item_id = item_id
        self.high = high


@app.before_request
def initialize_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=delete_old_price_history, trigger="interval", minutes=5)
    scheduler.add_job(func=refresh_prices(), trigger="interval", minutes=1)# Run every 5 minutes
    scheduler.start()


def refresh_items():
    print("refreshing items")
    url = 'https://prices.runescape.wiki/api/v1/osrs/mapping'

    headers = {
        'User-Agent': 'Price Drop Finder - @larkant on Discord',
    }

    mapping_response = requests.get(url, headers=headers)
    mapping_list = mapping_response.json()
    for i in mapping_list:
        found_id = Items.query.filter_by(id=i['id']).first()
        if found_id:
            pass
        else:
            if 'limit' in i and 'highalch' in i:
                add_item = Items(i['id'], i['name'], i['limit'], i['highalch'], 0, 0, 0)
                db.session.add(add_item)
                db.session.commit()
            elif 'limit' in i and 'highalch' not in i:
                add_item = Items(i['id'], i['name'], i['limit'], 0, 0, 0, 0)
                db.session.add(add_item)
                db.session.commit()
            elif 'limit' not in i and 'highalch' in i:
                add_item = Items(i['id'], i['name'], 0, i['highalch'], 0, 0, 0)
                db.session.add(add_item)
                db.session.commit()

    refresh_prices()

    items = Items.query.all()
    for i in items:
        found_id_delete = Items.query.filter_by(id=i.id).first()
        if found_id_delete.high == 0 and found_id_delete.low == 0:
            db.session.delete(found_id_delete)
            db.session.commit()

    print('items refreshed')

def price_drop_check():
        pass

def refresh_prices():
    print('Refreshing prices')
    url = 'https://prices.runescape.wiki/api/v1/osrs/latest'

    headers = {
        'User-Agent': 'Price Drop Finder - @larkant on Discord',
    }

    price_response = requests.get(url, headers=headers)
    js = price_response.json()
    price_json = js['data']

    for i in price_json:
        high = price_json[i]['low']
        low = price_json[i]['high']
        found_id_items = Items.query.filter_by(id=i).first()
        if found_id_items:
            found_id_items.high = high
            found_id_items.low = low
            if high != 0 and low != 0:
                found_id_items.margin = high-low
            else:
                found_id_items.margin = 1
            db.session.commit()

        new_price_history = PriceHistory(item_id=i, high=high)
        db.session.add(new_price_history)
        db.session.commit()

    print('Prices Refreshed')


def delete_old_price_history():
    cutoff_time = datetime.utcnow() - timedelta(minutes=5)
    old_records = PriceHistory.query.filter(PriceHistory.timestamp < cutoff_time).all()

    for record in old_records:
        db.session.delete(record)
    db.session.commit()
    print(f"Deleted {len(old_records)} records older than 5 minutes.")


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
            found_name = Users.query.filter_by(name=session_name).first()
        return render_template('user.html', user=username, email=None)


    else:
        return redirect(url_for('login'))

@app.route('/signup', methods = ['POST', 'GET'])
def signup():
    if request.method == 'POST':
        form_user = request.form['username']
        form_password = request.form['password']

        if form_user and form_password != '' or None:
            add_usr = Users(form_user, form_password)
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
            found_user = Users.query.filter_by(name=form_user).first()
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


@app.route('/api/data')
def data():
    return {'data': [user.to_dict() for user in Items.query]}


@app.route("/database")
def view_db():
    return render_template('view_db.html', values=Users.query.all())



if __name__ == "__main__":
    # Set this to true to refresh the items database with new OSRS items
    refresh_items_toggle = False

    with app.app_context():
        db.create_all()
        if refresh_items_toggle:
            refresh_items()
        refresh_prices()
        app.run(debug=True)


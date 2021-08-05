# all imports
import hmac
import sqlite3
import datetime

from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_mail import Mail, Message


# User class
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# Product class
class Product(object):
    def __init__(self, prod_id, prod_name, prod_price, prod_desc, prod_type):
        self.prod_id = prod_id
        self.prod_name = prod_name
        self.prod_price = prod_price
        self.prod_desc = prod_desc
        self.prod_type = prod_type


def fetch_users():
    with sqlite3.connect('PoS.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


# creating user table with sql in database
def init_user_table():
    conn = sqlite3.connect('PoS.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "email TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


# creating product table with sql in database
def init_product_table():
    conn = sqlite3.connect('PoS.db')
    print("Database opened successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS product(product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "product_name TEXT NOT NULL,"
                 "product_price TEXT NOT NULL,"
                 "product_description TEXT NOT NULL,"
                 "product_type TEXT NOT NULL)")
    print("table created successfully")
    conn.close()


init_user_table()
init_product_table()
users = fetch_users()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(hours=12)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'adamafrica.dev@gmail.com'
app.config['MAIL_PASSWORD'] = 'TaxiDriver8'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

jwt = JWT(app, authenticate, identity)


@app.route('/register/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if not first_name or not last_name or not email or not username or not password:
            response["message"] = "Error, please fill all fields."
            response["status_code"] = 400

        with sqlite3.connect("PoS.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "email,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?, ?)", (first_name, last_name, email, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201

            mail = Mail(app)
            msg = Message("Welcome!", sender='adamafrica.dev@gmail.com', recipients=[email])
            msg.body = "Hi there {}!\n".format(username)
            msg.body = msg.body + "Your profile has been registered successfully\n"
            msg.body = msg.body + "Please feel free to send us email if you have any queries or concerns.\n\n " \
                                  "Kind regards,\n Shopify Team"
            mail.send(msg)
        return response


@app.route('/login/', methods=["POST"])
def login():
    response = {}

    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect("PoS.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE username='{}' AND password='{}'".format(username, password))
            user_info = cursor.fetchone()

        if user_info:
            response['user_info'] = user_info
            response['message'] = "Success"
            response['status_code'] = 201
            return jsonify(response)

        else:
            response['message'] = "Login Unsuccessful, please try again"
            response['status_code'] = 401
            return jsonify(response)


@app.route('/add-product/', methods=["POST"])
@jwt_required()
def add_product():
    response = {}
    try:
        if request.method == "POST":
            product_name = request.form["product_name"]
            product_price = request.form["product_price"]
            product_description = request.form["product_description"]
            product_type = request.form["product_type"]

            if not product_name or not product_price or not product_description or not product_type:
                response["message"] = "Error, please fill all fields."
                response["status_code"] = 400

            int(product_price)

            with sqlite3.connect('PoS.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO product("
                               "product_name,"
                               "product_price,"
                               "product_description,"
                               "product_type) VALUES(?, ?, ?, ?)",
                               (product_name, product_price, product_description, product_type))
                conn.commit()
                response["status_code"] = 201
                response['description'] = "Product added successfully"
            return response
    except ValueError:
        response['message'] = "Error, please make sure price field is a number."
        response['status_code'] = 401
        return response


@app.route('/show-products/', methods=["GET"])
def get_product():
    response = {}
    with sqlite3.connect("PoS.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product")

        products = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = products
    return response


@app.route('/view-product/<int:product_id>/')
def view_product(product_id):
    response = {}

    with sqlite3.connect('PoS.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM product WHERE product_id={}'.format(product_id))
        product = cursor.fetchone()

    response['message'] = 'Product info fetched.'
    response['status_code'] = 200
    response['product'] = product

    return response


@app.route('/edit-product/<int:product_id>/', methods=['PUT'])
@jwt_required()
def edit_product(product_id):
    response = {}

    if request.method == 'PUT':
        incoming_data = dict(request.json)
        put_data = {}

        if incoming_data.get('product_name'):
            put_data['product_name'] = incoming_data.get('product_name')
            with sqlite3.connect('PoS.db') as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE product SET product_name=? WHERE product_id=?", (put_data["product_name"],
                                                                                        product_id))
                conn.commit()
                response['message'] = "Changes successfully made."
                response['status_code'] = 200

        if incoming_data.get('product_price'):
            put_data['product_price'] = incoming_data.get('product_price')
            with sqlite3.connect('PoS.db') as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE product SET product_price=? WHERE product_id=?", (put_data["product_price"],
                                                                                         product_id))
                conn.commit()
                response['message'] = "Changes successfully made."
                response['status_code'] = 200

        if incoming_data.get('product_description'):
            put_data['product_description'] = incoming_data.get('product_description')
            with sqlite3.connect('pointOfSale.db') as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE product SET product_description=? WHERE product_id=?",
                               (put_data["product_description"], product_id))
                conn.commit()
                response['message'] = "Changes successfully made."
                response['status_code'] = 200

        if incoming_data.get('product_type'):
            put_data['product_type'] = incoming_data.get('product_type')
            with sqlite3.connect('PoS.db') as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE product SET product_type=? WHERE product_id=?",
                               (put_data["product_type"], product_id))
                conn.commit()
                response['message'] = "Changes successfully made."
                response['status_code'] = 200

    return response


@app.route('/delete-product/<int:product_id>/')
@jwt_required()
def delete_product(product_id):
    response = {}

    with sqlite3.connect('PoS.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM product WHERE product_id={}'.format(product_id))
        conn.commit()

        response['message'] = 'Product successfully removed.'
        response['status_code'] = 200

    return response


if __name__ == '__main__':
    app.run()

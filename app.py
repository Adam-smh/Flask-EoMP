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
    def __init__(self, product_id, product_name, product_price, product_description, product_type, user_id):
        self.product_id = product_id
        self.product_name = product_name
        self.product_price = product_price
        self.product_description = product_description
        self.product_type = product_type
        self.user_id = user_id


class Database(object):
    def __init__(self):
        self.conn = sqlite3.connect('PoS.db')
        self.cursor = self.conn.cursor()

    def user_registration(self, first_name, last_name, email, username, password):
        self.cursor.execute("INSERT INTO user("
                            "first_name,"
                            "last_name,"
                            "email,"
                            "username,"
                            "password) VALUES(?, ?, ?, ?, ?)", (first_name, last_name, email, username, password))
        self.conn.commit()

        msg = Message("Welcome!", sender='adamafrica.dev@gmail.com', recipients=[email])
        msg.body = "Hi there {}!\n".format(username)
        msg.body = msg.body + "Your profile has been registered successfully\n"
        msg.body = msg.body + "Please feel free to send us email if you have any queries or concerns.\n\n " \
                              "Kind regards,\n Shopify Team"
        mail.send(msg)

    def add_product(self, product_name, product_price, product_description, product_type, user_id):
        self.cursor.execute("INSERT INTO product("
                            "product_name,"
                            "product_price,"
                            "product_description,"
                            "product_type"
                            "user_id) VALUES(?, ?, ?, ?, ?)",
                            (product_name, product_price, product_description, product_type, user_id))
        self.conn.commit()

    def get_product(self):
        self.cursor.execute("SELECT * FROM product")
        return self.cursor.fetchall()

    def view_product(self, product_id):
        self.cursor.execute('SELECT * FROM product WHERE product_id={}'.format(product_id))
        return self.cursor.fetchone()

    def edit_product(self, product_data, product_id):
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

    def delete_product(self, product_id):
        with sqlite3.connect('PoS.db') as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM product WHERE product_id={}'.format(product_id))
            conn.commit()


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
                 "product_type TEXT NOT NULL,"
                 "FOREIGN KEY (user_id)"
                 "REFERENCES user(user_id))")
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

mail = Mail(app)
jwt = JWT(app, authenticate, identity)


@app.route('/register/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        email = request.json['email']
        username = request.json['username']
        password = request.json['password']

        if not first_name or not last_name or not email or not username or not password:
            response["message"] = "Error, please fill all fields."
            response["status_code"] = 400
            return response

        db = Database()
        db.user_registration(first_name, last_name, email, username, password)

        response["message"] = "Registration Successful"
        response["status_code"] = 200
        return response


@app.route('/add-product/', methods=["POST"])
@jwt_required()
def add_product():
    response = {}
    try:
        if request.method == "POST":
            product_name = request.json["product_name"]
            product_price = request.json["product_price"]
            product_description = request.json["product_description"]
            product_type = request.json["product_type"]
            user_id = request.json["user_id"]

            int(product_price)

            if not product_name or not product_price or not product_description or not product_type:
                response["message"] = "Error, please fill all fields."
                response["status_code"] = 400
                return response

            db = Database()
            db.add_product(product_name, product_price, product_description, product_type, user_id)

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

    db = Database()

    response['products'] = db.get_product()
    response['message'] = "Products fetched successfully."
    response['status_code'] = 200
    return response


@app.route('/view-product/<int:product_id>/')
def view_product(product_id):
    response = {}

    db = Database()
    product = db.view_product(product_id)

    response['message'] = 'Product info fetched.'
    response['status_code'] = 200
    response['product'] = product

    return response


@app.route('/edit-product/<int:product_id>/', methods=['PUT'])
@jwt_required()
def edit_product(product_id):
    response = None

    if request.method == 'PUT':
        incoming_data = dict(request.json)
        db = Database()
        response = db.edit_product(incoming_data, product_id)

    return response


@app.route('/delete-product/<int:product_id>/')
@jwt_required()
def delete_product(product_id):
    response = {}

    db = Database()
    db.delete_product(product_id)

    response['message'] = 'Product successfully removed.'
    response['status_code'] = 200

    return response


if __name__ == '__main__':
    app.run(debug=True)

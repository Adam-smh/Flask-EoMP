import hmac
import sqlite3
import datetime

from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect('PoS.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


def init_user_table():
    conn = sqlite3.connect('PoS.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


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

jwt = JWT(app, authenticate, identity)


@app.route('/register/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect("PoS.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?)", (first_name, last_name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
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

    if request.method == "POST":
        p_id = request.form["p_id"]
        p_name = request.form["p_name"]
        p_price = request.form["p_price"]
        p_description = request.form["p_description"]
        p_type = request.form["p_type"]

        with sqlite3.connect('PoS.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO product("
                           "product_id,"
                           "product_name,"
                           "product_price,"
                           "product_description,"
                           "product_type) VALUES(?, ?, ?)", (p_id, p_name, p_price, p_description, p_type))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "Product added successfully"
        return response


# @app.route('/get-product/', methods=["GET"])
# def get_product():
#     response = {}
#     with sqlite3.connect("PoS.db") as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM post")
#
#         posts = cursor.fetchall()
#
#     response['status_code'] = 200
#     response['data'] = posts
#     return response


if __name__ == '__main__':
    app.run()

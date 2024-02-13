import random
import string
from datetime import datetime, timedelta
import sqlite3

import flask
import json
import os

# Generate random key consisting of letters and numbers
def generate_key(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# Add key to the database with an expiration date of 1 day
def add_key_to_database(key):
    expiration_date = datetime.now() + timedelta(days=1)
    conn = sqlite3.connect('keys.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS keys (key TEXT, expiration_date TEXT)''')
    cursor.execute('''INSERT INTO keys VALUES (?, ?)''', (key, expiration_date))
    conn.commit()
    conn.close()
    return key, expiration_date

# Check if key exists in the database and is not expired
def is_valid_key(key):
    conn = sqlite3.connect('keys.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT expiration_date FROM keys WHERE key = ?''', (key,))
    result = cursor.fetchone()
    conn.close()

    if result:
        expiration_date = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
        if expiration_date > datetime.now():
            return True

FILE_PATH = 'users.json'

def load_data():
    data = {}
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r') as file:
                data = json.load(file)
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            print("Error loading JSON data. Initializing an empty dictionary.")
    return data

def save_data(data):
    with open(FILE_PATH, 'w') as file:
        json.dump(data, file)

def add_ip(ip_address):
    data = load_data()
    if ip_address not in data:
        data[ip_address] = str(datetime.now() - timedelta(seconds=2))
        save_data(data)
        print("New IP added successfully.")
    else:
        print("IP already exists in the database.")

def update_last_key(ip_address):
    data = load_data()
    if ip_address in data:
        data[ip_address] = str(datetime.now())
        save_data(data)
        print("Last key updated successfully.")
    else:
        print("IP does not exist in the database.")

def check_last_key(ip_address):
    data = load_data()
    if ip_address in data:
        last_key_time = datetime.strptime(data[ip_address], "%Y-%m-%d %H:%M:%S.%f")
        if datetime.now() - last_key_time > timedelta(seconds=2):
            return True
        else:
            return False
    else:
        return False

if __name__ == "__main__":
    print(add_key_to_database(generate_key(50)))
    
    app = flask.Flask(__file__)

    @app.route("/api/check_key", methods=["POST"])
    def api_check_key():
        key = flask.request.json.get("key")
        if is_valid_key(key):
            return flask.jsonify({
                "valid": True
                })
            
        else:
            return flask.jsonify({
                "valid": False
            })
            
    @app.route("/api/get_key")
    def get_new_key():
        ip = flask.request.environ['REMOTE_ADDR']        
        add_ip(ip)
        print(check_last_key(ip), "<-- PRO COD3R")
        if check_last_key(ip):
            key = generate_key(50)
            add_key_to_database(key)
            update_last_key(ip)
            return flask.jsonify({
                "key": key
            })
        else:
            return flask.jsonify({
                "message": "you need to wait 2s between each key."
            })
    
    app.run()
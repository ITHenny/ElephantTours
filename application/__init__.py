from flask import Flask
import psycopg2
import psycopg2.extras
from application import views
from application import config
import os
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

imgFolder = os.path.join('static', 'img')

pg = psycopg2.connect(
    host="localhost",
    dbname="ElephantTours",
    user="postgres",
    password=config.SQL_PASSWORD,
    port=5432,
)

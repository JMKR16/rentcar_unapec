import os
from flask_mysqldb import MySQL
from dotenv import load_dotenv

#  Carga el archivo .env automáticamente al arrancar
load_dotenv()

def configurar_db(app):

    # Se  leen  variables directamente desde el archivo .env
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('DB_NAME') if os.getenv('DB_NAME') else os.getenv('MYSQL_DB')
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    
    #  Clave secreta fija para proteger las sesiones de cookies del Login
    app.config['SECRET_KEY'] = 'unapec_rentcar_secret_key_2026'
    
    mysql = MySQL(app)
    return mysql
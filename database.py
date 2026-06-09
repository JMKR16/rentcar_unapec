from flask_mysqldb import MySQL

def configurar_db(app):

    app.config['MYSQL_HOST'] = 'localhost'
    
   
    app.config['MYSQL_USER'] = 'root'
    
    
    app.config['MYSQL_PASSWORD'] = 'Mysql10616'
    
    
    app.config['MYSQL_DB'] = 'rentcar_unapec'
    
   
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    
    mysql = MySQL(app)
    return mysql
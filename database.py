from flask_mysqldb import MySQL

def configurar_db(app):
    # 1. Dirección del servidor (MI pc)
    app.config['MYSQL_HOST'] = 'localhost'
    
    # 2. Usuario administrador de MySQL
    app.config['MYSQL_USER'] = 'root'
    
    # 3. La contraseña del cliente de mysql de mi maquina
    app.config['MYSQL_PASSWORD'] = 'Mysql10616'
    
    # 4. El nombre exacto de la base de datos creada
    app.config['MYSQL_DB'] = 'rentcar_unapec'
    
    # 5. Formato de respuesta: Le pedimos a MySQL que nos devuelva los datos 
    # en forma de "Diccionario" de Python (Clave: Valor), que es más fácil de leer.
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    
    # Inicializa el conector
    mysql = MySQL(app)
    return mysql
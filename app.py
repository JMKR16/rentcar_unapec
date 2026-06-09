from flask import Flask, render_template
from database import configurar_db

app = Flask(__name__)

# Conectamos el puente
mysql = configurar_db(app)

@app.route('/')
def inicio():
    # 1. Abrimos la pestaña de consulta desde Python
    cursor = mysql.connection.cursor()
    
    # 2. Mandamos el comando SQL a la base de datos
    cursor.execute("SELECT * FROM clientes")
    
    # 3. Guardamos los resultados en una variable
    lista_clientes = cursor.fetchall()
    
    # 4. Cerramos la pestaña de consulta
    cursor.close()
    
    # 5. Lo imprimimos en la terminal de VS Code para comprobar
    print("DATOS DESDE MYSQL:", lista_clientes)
    
    return "<h1>¡El puente Flask-MySQL está funcionando! Revisa la terminal de VS Code.</h1>"

if __name__ == '__main__':
    app.run(debug=True)
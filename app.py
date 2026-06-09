from flask import Flask, render_template
from database import configurar_db

app = Flask(__name__)

# Conectar el puente de datos
mysql = configurar_db(app)

@app.route('/')
def inicio():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM clientes")
    lista_clientes = cursor.fetchall()
    cursor.close()
    
    # Aquí se le dice  a Flask que abra la plantilla y le inyecte los datos
    return render_template('clientes.html', clientes_pantalla=lista_clientes)

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for
from database import configurar_db

app = Flask(__name__)
mysql = configurar_db(app)


@app.route('/')
def inicio():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM clientes")
    lista_clientes = cursor.fetchall()
    cursor.close()
    return render_template('clientes.html', clientes_pantalla=lista_clientes)


@app.route('/guardar_cliente', methods=['POST'])
def guardar_cliente():
    nombre = request.form['txt_nombre']
    cedula = request.form['txt_cedula']
    tarjeta = request.form['txt_tarjeta']
    limite = request.form['txt_limite']
    tipo = request.form['sel_tipo']
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO clientes (nombre, cedula, no_tarjeta_cr, limite_credito, tipo_persona)
        VALUES (%s, %s, %s, %s, %s)
    """, (nombre, cedula, tarjeta, limite, tipo))
    
    mysql.connection.commit()
    cursor.close()
    

    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(debug=True)
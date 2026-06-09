from flask import Flask, render_template, request, redirect, url_for, flash
from database import configurar_db
import re

app = Flask(__name__)
app.secret_key = 'clave_secreta_temporal'
mysql = configurar_db(app)


def validar_nombre(nombre):
    if not nombre or len(nombre) > 100:
        return False, "El nombre debe tener entre 1 y 100 caracteres"
    if not re.match(r'^[A-Za-záéíóúñÑ ]+$', nombre):
        return False, "El nombre solo puede contener letras y espacios"
    return True, ""


def validar_cedula(cedula):
    if not re.match(r'^\d{3}-\d{7}-\d{1}$', cedula):
        return False, "Cédula inválida. Formato: 000-0000000-0"
    return True, ""


def validar_tarjeta(tarjeta):
    tarjeta_limpia = tarjeta.replace(' ', '')
    if not re.match(r'^\d{16}$', tarjeta_limpia):
        return False, "Tarjeta debe contener 16 dígitos"
    return True, ""


def validar_limite(limite):
    try:
        limite_float = float(limite)
        if limite_float < 0 or limite_float > 1000000:
            return False, "Límite debe estar entre 0 y 1,000,000"
        return True, ""
    except ValueError:
        return False, "Límite debe ser un número válido"


def validar_tipo(tipo):
    if tipo not in ['Física', 'Jurídica']:
        return False, "Tipo de persona inválido"
    return True, ""


@app.route('/')
def inicio():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM clientes")
        lista_clientes = cursor.fetchall()
        cursor.close()
        return render_template('clientes.html', clientes_pantalla=lista_clientes)
    except Exception as e:
        flash(f"Error al cargar clientes: {str(e)}", "danger")
        return render_template('clientes.html', clientes_pantalla=[])


@app.route('/guardar_cliente', methods=['POST'])
def guardar_cliente():
    nombre = request.form.get('txt_nombre', '').strip()
    cedula = request.form.get('txt_cedula', '').strip()
    tarjeta = request.form.get('txt_tarjeta', '').strip()
    limite = request.form.get('txt_limite', '').strip()
    tipo = request.form.get('sel_tipo', '').strip()

    valido, msg = validar_nombre(nombre)
    if not valido:
        flash(msg, "warning")
        return redirect(url_for('inicio'))

    valido, msg = validar_cedula(cedula)
    if not valido:
        flash(msg, "warning")
        return redirect(url_for('inicio'))

    valido, msg = validar_tarjeta(tarjeta)
    if not valido:
        flash(msg, "warning")
        return redirect(url_for('inicio'))

    valido, msg = validar_limite(limite)
    if not valido:
        flash(msg, "warning")
        return redirect(url_for('inicio'))

    valido, msg = validar_tipo(tipo)
    if not valido:
        flash(msg, "warning")
        return redirect(url_for('inicio'))

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO clientes (nombre, cedula, no_tarjeta_cr, limite_credito, tipo_persona)
            VALUES (%s, %s, %s, %s, %s)
        """, (nombre, cedula, tarjeta, limite, tipo))

        mysql.connection.commit()
        cursor.close()

        flash("Cliente guardado exitosamente", "success")
    except Exception as e:
        flash(f"Error al guardar cliente: {str(e)}", "danger")

    return redirect(url_for('inicio'))


if __name__ == '__main__':
    app.run(debug=True)
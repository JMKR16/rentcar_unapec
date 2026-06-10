from flask import Flask, render_template, request, redirect, url_for, flash
from database import configurar_db

app = Flask(__name__)
app.secret_key = 'clave_secreta_temporal' # Requerido para las alertas flash
mysql = configurar_db(app)

# ==========================================
#  SECCIÓN DE VEHÍCULOS (NUEVO BLOQUE)
# ==========================================

@app.route('/vehiculos')
def listar_vehiculos():
    try:
        cursor = mysql.connection.cursor()
        
        # CONSULTA REINA: Mapeada idéntica a tus columnas de Workbench
        query_vehiculos = """
            SELECT 
                v.id_vehiculo, v.descripcion, v.no_chasis, v.no_motor, v.no_placa,
                m.descripcion AS marca_nombre,
                mo.descripcion AS modelo_nombre,
                t.descripcion AS tipo_nombre,
                c.descripcion AS combustible_nombre
            FROM vehiculos v
            INNER JOIN marcas m ON v.id_marca = m.id_marca
            INNER JOIN modelos mo ON v.id_modelo = mo.id_modelo
            INNER JOIN tipos_vehiculos t ON v.id_tipo_vehiculo = t.id_tipo_vehiculo
            INNER JOIN tipos_combustible c ON v.id_combustible = c.id_combustible
        """
        cursor.execute(query_vehiculos)
        lista_vehiculos = cursor.fetchall()
        
        # JALAMOS LOS CATÁLOGOS PARA LOS DESPLEGABLES DEL MODAL
        cursor.execute("SELECT id_marca, descripcion FROM marcas")
        cat_marcas = cursor.fetchall()
        
        cursor.execute("SELECT id_modelo, descripcion FROM modelos")
        cat_modelos = cursor.fetchall()
        
        cursor.execute("SELECT id_tipo_vehiculo, descripcion FROM tipos_vehiculos")
        cat_tipos = cursor.fetchall()
        
        cursor.execute("SELECT id_combustible, descripcion FROM tipos_combustible")
        cat_combustibles = cursor.fetchall()
        
        cursor.close()
        
        return render_template('vehiculos.html', 
                               vehiculos_pantalla=lista_vehiculos,
                               marcas_form=cat_marcas,
                               modelos_form=cat_modelos,
                               tipos_form=cat_tipos,
                               combustibles_form=cat_combustibles)
                               
    except Exception as e:
        flash(f"Error al cargar el módulo de vehículos: {str(e)}", "danger")
        return render_template('vehiculos.html', vehiculos_pantalla=[], marcas_form=[], modelos_form=[], tipos_form=[], combustibles_form=[])


@app.route('/guardar_vehiculo', methods=['POST'])
def guardar_vehiculo():
    # Se capturan los textos e IDs relacionales enviados desde el modal
    descripcion = request.form.get('txt_descripcion', '').strip()
    chasis = request.form.get('txt_chasis', '').strip()
    motor = request.form.get('txt_motor', '').strip()
    placa = request.form.get('txt_placa', '').strip()
    
    id_marca = request.form.get('sel_marca')
    id_modelo = request.form.get('sel_modelo')
    id_tipo = request.form.get('sel_tipo')
    id_combustible = request.form.get('sel_combustible')
    
    
    if not descripcion or not chasis or not motor or not placa:
        flash("Todos los campos de texto son obligatorios", "warning")
        return redirect(url_for('listar_vehiculos'))
        
    try:
        cursor = mysql.connection.cursor()
        # Inserción relacional limpia en la tabla vehículos
        cursor.execute("""
            INSERT INTO vehiculos (descripcion, no_chasis, no_motor, no_placa, id_tipo_vehiculo, id_marca, id_modelo, id_combustible)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (descripcion, chasis, motor, placa, id_tipo, id_marca, id_modelo, id_combustible))
        
        mysql.connection.commit()
        cursor.close()
        
        flash("Vehículo relacional registrado exitosamente", "success")
    except Exception as e:
        flash(f"Error crítico al guardar en la base de datos: {str(e)}", "danger")
        
    return redirect(url_for('listar_vehiculos'))

# ==========================================
# CÓDIGO DE CLIENTES ANTERIOR 
# ==========================================

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


@app.route('/marcas')
def listar_marcas():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id_marca, descripcion FROM marcas ORDER BY id_marca ASC")
        marcas = cursor.fetchall()
        cursor.close()
        return render_template('marcas.html', lista_marcas=marcas)
    except Exception as e:
        flash(f"Error al cargar marcas: {str(e)}", "danger")
        return render_template('marcas.html', lista_marcas=[])


@app.route('/guardar_marca', methods=['POST'])
def guardar_marca():
    nombre_marca = request.form.get('txt_marca', '').strip()
    if not nombre_marca:
        flash("El nombre de la marca es obligatorio.", "warning")
        return redirect(url_for('listar_marcas'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO marcas (descripcion) VALUES (%s)", (nombre_marca,))
        mysql.connection.commit()
        cursor.close()
        flash(f"Marca '{nombre_marca}' registrada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al guardar marca: {str(e)}", "danger")
    return redirect(url_for('listar_marcas'))


# =======================
#  CRUD  MODELOS
# =======================

@app.route('/modelos')
def listar_modelos():
    try:
        cursor = mysql.connection.cursor()
        # Se necesitan las marcas para llenar el dropdown del formulario
        cursor.execute("SELECT id_marca, descripcion FROM marcas ORDER BY id_marca ASC")
        marcas = cursor.fetchall()
        
        # Se cargan los modelos cruzados con su marca
        query_modelos = """
            SELECT mo.id_modelo, mo.descripcion, m.descripcion AS marca_nombre 
            FROM modelos mo
            INNER JOIN marcas m ON mo.id_marca = m.id_marca
            ORDER BY mo.id_modelo ASC
        """
        cursor.execute(query_modelos)
        modelos = cursor.fetchall()
        cursor.close()
        return render_template('modelos.html', lista_marcas=marcas, lista_modelos=modelos)
    except Exception as e:
        flash(f"Error al cargar modelos: {str(e)}", "danger")
        return render_template('modelos.html', lista_marcas=[], lista_modelos=[])


@app.route('/guardar_modelo', methods=['POST'])
def guardar_modelo():
    id_marca = request.form.get('sel_marca')
    nombre_modelo = request.form.get('txt_modelo', '').strip()
    if not id_marca or not nombre_modelo:
        flash("Todos los campos son obligatorios.", "warning")
        return redirect(url_for('listar_modelos'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO modelos (id_marca, descripcion) VALUES (%s, %s)", (id_marca, nombre_modelo))
        mysql.connection.commit()
        cursor.close()
        flash(f"Modelo '{nombre_modelo}' guardado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al guardar modelo: {str(e)}", "danger")
    return redirect(url_for('listar_modelos'))

if __name__ == '__main__':
    app.run(debug=True)
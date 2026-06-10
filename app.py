from flask import Flask, render_template, request, redirect, url_for, flash
from database import configurar_db

app = Flask(__name__)
app.secret_key = 'clave_secreta_temporal' # Requerido para las alertas flash
mysql = configurar_db(app)

# ======================================
#  CÓDIGO DE CLIENTES (Pestaña Inicio)
# ======================================
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


# ==========================================
#  CRUD: TIPOS DE VEHÍCULOS
# ==========================================

@app.route('/tipos_vehiculos')
def listar_tipos_vehiculos():
    try:
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        if filtro == 'todos':
            cursor.execute("SELECT id_tipo_vehiculo, descripcion, estado FROM tipos_vehiculos ORDER BY id_tipo_vehiculo ASC")
        else:
            cursor.execute("SELECT id_tipo_vehiculo, descripcion, estado FROM tipos_vehiculos WHERE estado = 'Activo' ORDER BY id_tipo_vehiculo ASC")
            
        tipos = cursor.fetchall()
        cursor.close()
        return render_template('tipos_vehiculos.html', lista_tipos=tipos, filtro_actual=filtro)
    except Exception as e:
        flash(f"Error al cargar tipos: {str(e)}", "danger")
        return render_template('tipos_vehiculos.html', lista_tipos=[], filtro_actual='activos')

@app.route('/guardar_tipo_vehiculo', methods=['POST'])
def guardar_tipo_vehiculo():
    descripcion = request.form.get('txt_descripcion', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    if not descripcion:
        flash("La descripción es obligatoria.", "warning")
        return redirect(url_for('listar_tipos_vehiculos'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO tipos_vehiculos (descripcion, estado) VALUES (%s, %s)", (descripcion, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Tipo '{descripcion}' registrado con éxito.", "success")
    except Exception as e:
        flash(f"Error al guardar tipo: {str(e)}", "danger")
    return redirect(url_for('listar_tipos_vehiculos'))

@app.route('/cambiar_estado_tipo/<int:id_tipo>/<string:nuevo_estado>')
def cambiar_estado_tipo(id_tipo, nuevo_estado):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE tipos_vehiculos SET estado = %s WHERE id_tipo_vehiculo = %s", (nuevo_estado, id_tipo))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del tipo de vehículo actualizado a '{nuevo_estado}'.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('listar_tipos_vehiculos'))

# ===================================
#  CRUD MARCAS 
# ===================================

@app.route('/marcas')
def listar_marcas():
    try:
        # Se captura si el usuario quiere ver 'todos' o solo los 'activos' (por defecto solo activos)
        filtro = request.args.get('ver', 'activos')
        
        cursor = mysql.connection.cursor()
        
        if filtro == 'todos':
            # Trae absolutamente todo (Activos e Inactivos)
            cursor.execute("SELECT id_marca, descripcion, estado FROM marcas ORDER BY id_marca ASC")
        else:
            
            cursor.execute("SELECT id_marca, descripcion, estado FROM marcas WHERE estado = 'Activo' ORDER BY id_marca ASC")
            
        marcas = cursor.fetchall()
        cursor.close()
        
        return render_template('marcas.html', lista_marcas=marcas, filtro_actual=filtro)
    except Exception as e:
        flash(f"Error al cargar marcas: {str(e)}", "danger")
        return render_template('marcas.html', lista_marcas=[], filtro_actual='activos')

@app.route('/guardar_marca', methods=['POST'])
def guardar_marca():
    nombre_marca = request.form.get('txt_marca', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    
    if not nombre_marca:
        flash("El nombre de la marca es obligatorio.", "warning")
        return redirect(url_for('listar_marcas'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO marcas (descripcion, estado) VALUES (%s, %s)", (nombre_marca, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Marca '{nombre_marca}' registrada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al guardar marca: {str(e)}", "danger")
    return redirect(url_for('listar_marcas'))

@app.route('/cambiar_estado_marca/<int:id_marca>/<string:nuevo_estado>')
def cambiar_estado_marca(id_marca, nuevo_estado):
    try:
        cursor = mysql.connection.cursor()

        # Se Ejecuta el Soft Delete o la reactivación lógica sin romper llaves foráneas
        cursor.execute("UPDATE marcas SET estado = %s WHERE id_marca = %s", (nuevo_estado, id_marca))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado de la marca actualizado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al cambiar el estado de la marca: {str(e)}", "danger")
    return redirect(url_for('listar_marcas'))


# ==================================
# 3.  CRUD: MODELOS 
# ==================================

@app.route('/modelos')
def listar_modelos():
    try:
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        # El modal para CREAR modelos siempre debe jalar solo marcas ACTIVAS por seguridad
        cursor.execute("SELECT id_marca, descripcion FROM marcas WHERE estado = 'Activo' ORDER BY id_marca ASC")
        marcas = cursor.fetchall()
        
        # Filtra la tabla de modelos según el botón seleccionado
        if filtro == 'todos':
            query_modelos = """
                SELECT mo.id_modelo, mo.descripcion, m.descripcion AS marca_nombre, mo.estado 
                FROM modelos mo
                INNER JOIN marcas m ON mo.id_marca = m.id_marca
                ORDER BY mo.id_modelo ASC
            """
        else:
            query_modelos = """
                SELECT mo.id_modelo, mo.descripcion, m.descripcion AS marca_nombre, mo.estado 
                FROM modelos mo
                INNER JOIN marcas m ON mo.id_marca = m.id_marca
                WHERE mo.estado = 'Activo'
                ORDER BY mo.id_modelo ASC
            """
            
        cursor.execute(query_modelos)
        modelos = cursor.fetchall()
        cursor.close()
        return render_template('modelos.html', lista_marcas=marcas, lista_modelos=modelos, filtro_actual=filtro)
    except Exception as e:
        flash(f"Error al cargar modelos: {str(e)}", "danger")
        return render_template('modelos.html', lista_marcas=[], lista_modelos=[], filtro_actual='activos')

@app.route('/guardar_modelo', methods=['POST'])
def guardar_modelo():
    id_marca = request.form.get('sel_marca')
    nombre_modelo = request.form.get('txt_modelo', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    if not id_marca or not nombre_modelo:
        flash("Todos los campos son obligatorios.", "warning")
        return redirect(url_for('listar_modelos'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO modelos (id_marca, descripcion, estado) VALUES (%s, %s, %s)", (id_marca, nombre_modelo, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Modelo '{nombre_modelo}' registrado con éxito.", "success")
    except Exception as e:
        flash(f"Error al guardar modelo: {str(e)}", "danger")
    return redirect(url_for('listar_modelos'))

@app.route('/cambiar_estado_modelo/<int:id_modelo>/<string:nuevo_estado>')
def cambiar_estado_modelo(id_modelo, nuevo_estado):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE modelos SET estado = %s WHERE id_modelo = %s", (nuevo_estado, id_modelo))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del modelo actualizado a '{nuevo_estado}'.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('listar_modelos'))


# ==========================================
#  CRUD: TIPOS DE COMBUSTIBLE 
# ==========================================

@app.route('/tipos_combustible')
def listar_combustibles():
    try:
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        if filtro == 'todos':
            cursor.execute("SELECT id_combustible, descripcion, estado FROM tipos_combustible ORDER BY id_combustible ASC")
        else:
            cursor.execute("SELECT id_combustible, descripcion, estado FROM tipos_combustible WHERE estado = 'Activo' ORDER BY id_combustible ASC")
            
        combustibles = cursor.fetchall()
        cursor.close()
        return render_template('tipos_combustible.html', lista_combustibles=combustibles, filtro_actual=filtro)
    except Exception as e:
        flash(f"Error al cargar tipos de combustible: {str(e)}", "danger")
        return render_template('tipos_combustible.html', lista_combustibles=[], filtro_actual='activos')

@app.route('/guardar_combustible', methods=['POST'])
def guardar_combustible():
    descripcion = request.form.get('txt_descripcion', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    
    if not descripcion:
        flash("La descripción del combustible es obligatoria.", "warning")
        return redirect(url_for('listar_combustibles'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO tipos_combustible (descripcion, estado) VALUES (%s, %s)", (descripcion, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Combustible '{descripcion}' registrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al guardar tipo de combustible: {str(e)}", "danger")
    return redirect(url_for('listar_combustibles'))

@app.route('/cambiar_estado_combustible/<int:id_combustible>/<string:nuevo_estado>')
def cambiar_estado_combustible(id_combustible, nuevo_estado):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE tipos_combustible SET estado = %s WHERE id_combustible = %s", (nuevo_estado, id_combustible))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del combustible actualizado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al cambiar el estado del combustible: {str(e)}", "danger")
    return redirect(url_for('listar_combustibles'))

# ==========================================
#  CRUD VEHÍCULOS 
# ==========================================
@app.route('/vehiculos')
def listar_vehiculos():
    try:
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        #  Se toman los catalogos protegidos (Solo los que estén ACTIVOS)
        cursor.execute("SELECT id_marca, descripcion FROM marcas WHERE estado = 'Activo' ORDER BY descripcion ASC")
        cat_marcas = cursor.fetchall()
        
        cursor.execute("SELECT id_modelo, descripcion, id_marca FROM modelos WHERE estado = 'Activo'")
        cat_modelos = cursor.fetchall()
        
        cursor.execute("SELECT id_tipo_vehiculo, descripcion FROM tipos_vehiculos WHERE estado = 'Activo' ORDER BY descripcion ASC")
        cat_tipos = cursor.fetchall()
        
        cursor.execute("SELECT id_combustible, descripcion FROM tipos_combustible WHERE estado = 'Activo' ORDER BY descripcion ASC")
        cat_combustibles = cursor.fetchall()
        
        #  Se construye el query  de la tabla relacional CON INNER JOINS
        query_base = """
            SELECT 
                v.id_vehiculo, v.descripcion, v.no_chasis, v.no_motor, v.no_placa,
                m.descripcion AS marca_nombre,
                mo.descripcion AS modelo_nombre,
                t.descripcion AS tipo_nombre,
                c.descripcion AS combustible_nombre,
                v.estado
            FROM vehiculos v
            INNER JOIN marcas m ON v.id_marca = m.id_marca
            INNER JOIN modelos mo ON v.id_modelo = mo.id_modelo
            INNER JOIN tipos_vehiculos t ON v.id_tipo_vehiculo = t.id_tipo_vehiculo
            INNER JOIN tipos_combustible c ON v.id_combustible = c.id_combustible
        """
        
        #  Filtro de Soft Delete sobre la tabla de vehículos
        if filtro == 'todos':
            query_vehiculos = query_base + " ORDER BY v.id_vehiculo ASC"
        else:
            query_vehiculos = query_base + " WHERE v.estado = 'Activo' ORDER BY v.id_vehiculo ASC"
            
        cursor.execute(query_vehiculos)
        lista_vehiculos = cursor.fetchall()
        cursor.close()
        
        return render_template('vehiculos.html', 
                               vehiculos_pantalla=lista_vehiculos,
                               marcas_form=cat_marcas,
                               modelos_form=cat_modelos,
                               tipos_form=cat_tipos,
                               combustibles_form=cat_combustibles,
                               filtro_actual=filtro)
                               
    except Exception as e:
        flash(f"Error crítico al cargar el módulo relacional de vehículos: {str(e)}", "danger")
        return render_template('vehiculos.html', vehiculos_pantalla=[], marcas_form=[], modelos_form=[], tipos_form=[], combustibles_form=[], filtro_actual='activos')


@app.route('/guardar_vehiculo', methods=['POST'])
def guardar_vehiculo():
    descripcion = request.form.get('txt_descripcion', '').strip()
    chasis = request.form.get('txt_chasis', '').strip()
    motor = request.form.get('txt_motor', '').strip()
    placa = request.form.get('txt_placa', '').strip()
    
    id_marca = request.form.get('sel_marca')
    id_modelo = request.form.get('sel_modelo')
    id_tipo = request.form.get('sel_tipo')
    id_combustible = request.form.get('sel_combustible')
    estado = request.form.get('sel_estado', 'Activo')
    
    if not descripcion or not chasis or not motor or not placa or not id_marca or not id_modelo or not id_tipo or not id_combustible:
        flash("Todos los campos relacionales y de texto son obligatorios.", "warning")
        return redirect(url_for('listar_vehiculos'))
        
    try:
        cursor = mysql.connection.cursor()
        
        # VALIDACIÓN DE PLACA ÚNICA
        cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE no_placa = %s", (placa,))
        placa_existente = cursor.fetchone()
        
        if placa_existente:
            cursor.close()
            flash(f"Error: La placa '{placa}' ya está registrada en el sistema con otro vehículo.", "danger")
            return redirect(url_for('listar_vehiculos'))
            
        # Si no existe, procedemos con la inserción normal
        cursor.execute("""
            INSERT INTO vehiculos (descripcion, no_chasis, no_motor, no_placa, id_tipo_vehiculo, id_marca, id_modelo, id_combustible, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (descripcion, chasis, motor, placa, id_tipo, id_marca, id_modelo, id_combustible, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Vehículo '{descripcion}' [Placa: {placa}] registrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al insertar el vehículo: {str(e)}", "danger")
        
    return redirect(url_for('listar_vehiculos'))

@app.route('/cambiar_estado_vehiculo/<int:id_vehiculo>/<string:nuevo_estado>')
def cambiar_estado_vehiculo(id_vehiculo, nuevo_estado):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE vehiculos SET estado = %s WHERE id_vehiculo = %s", (nuevo_estado, id_vehiculo))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del vehículo ID {id_vehiculo} actualizado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al cambiar el estado del vehículo: {str(e)}", "danger")
    return redirect(url_for('listar_vehiculos'))

# ======================
#   CIERRE  DEL ARCHIVO
# =======================
if __name__ == '__main__':
    app.run(debug=True)
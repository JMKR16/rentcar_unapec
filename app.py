from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import configurar_db

app = Flask(__name__)
app.secret_key = 'clave_secreta_temporal' # Requerido para las alertas flash
mysql = configurar_db(app)


# ==========================================
#  SEGURIDAD Y CONTROL DE ACCESO (LOGIN)
# ==========================================

@app.route('/')
def login():
    # Si ya inició sesión, se es redirigido directo a clientes
    if 'usuario_id' in session:
        return redirect(url_for('dashboard')) #  Cambiado a dashboard
    return render_template('login.html')

@app.route('/autenticar', methods=['POST'])
def autenticar():
    correo = request.form.get('txt_correo', '').strip()
    clave = request.form.get('txt_clave', '').strip()
    
    if not correo or not clave:
        flash("Por favor, llene todos los campos.", "warning")
        return redirect(url_for('login'))
        
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id_usuario, nombre, clave, estado FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        cursor.close()
        
        # Al usar DictCursor, valida los campos como diccionario
        if usuario and usuario['clave'] == clave:
            if usuario['estado'] != 'Activo':
                flash("Este usuario se encuentra inactivo.", "danger")
                return redirect(url_for('login'))
                
            # Se guardan los datos en la sesión global de Flask
            session['usuario_id'] = usuario['id_usuario']
            session['usuario_nombre'] = usuario['nombre']
            flash(f"¡Bienvenido al sistema, {usuario['nombre']}!", "success")
            return redirect(url_for('dashboard')) # Redirige al dashboard en lugar de clientes
        else:
            flash("Correo o contraseña incorrectos.", "danger")
            return redirect(url_for('login'))
            
    except Exception as e:
        flash(f"Error de autenticación: {str(e)}", "danger")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear() # Limpia las cookies de sesión
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('login'))


# ==========================================
#  DASHBOARD / PANEL DE CONTROL PRINCIPAL
# ==========================================
@app.route('/dashboard')
def dashboard():
   
    if 'usuario_id' not in session:
        flash("Por favor, inicie sesión para acceder al sistema.", "danger")
        return redirect(url_for('login'))
        
    try:
        cursor = mysql.connection.cursor()
        
        # Cuenta a los  Clientes Activos
        cursor.execute("SELECT COUNT(*) AS total FROM clientes WHERE estado = 'Activo'")
        total_clientes = cursor.fetchone()['total']
        
        # Cuenta a los  Vehículos Totales
        cursor.execute("SELECT COUNT(*) AS total FROM vehiculos WHERE estado = 'Activo'")
        total_vehiculos = cursor.fetchone()['total']
        
        # Cuenta a los Empleados Activos
        cursor.execute("SELECT COUNT(*) AS total FROM empleados WHERE estado = 'Activo'")
        total_empleados = cursor.fetchone()['total']
        
        # Cuenta las Inspecciones Realizadas
        cursor.execute("SELECT COUNT(*) AS total FROM inspecciones")
        total_inspecciones = cursor.fetchone()['total']
        
        cursor.close()
        
        # Renderiza la nueva plantilla pasando todas las variables estadísticas
        return render_template('dashboard.html', 
                               clientes=total_clientes, 
                               vehiculos=total_vehiculos, 
                               empleados=total_empleados,
                               inspecciones=total_inspecciones)
                               
    except Exception as e:
        flash(f"Error al cargar las métricas del dashboard: {str(e)}", "danger")
        return render_template('dashboard.html', clientes=0, vehiculos=0, empleados=0, inspecciones=0)

# =================================================================================
# Función de validación de cédula dominicana según el algoritmo oficial de la JCE
# =================================================================================

def validar_cedula_dominicana(cedula_str):
    #  Limpia guiones y espacios por si vienen en el texto
    cedula = cedula_str.replace("-", "").strip()
    
    #  Valida que tenga exactamente 11 dígitos numéricos
    if len(cedula) != 11 or not cedula.isdigit():
        return False
        
    #  Patrón de multiplicación oficial de la JCE
    multiplicadores = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1]
    total_suma = 0
    
    #  Recorre y aplica el algoritmo
    for i in range(11):
        digito = int(cedula[i])
        producto = digito * multiplicadores[i]
        
        # Si el producto da 10 o más, suma sus dígitos individuales
        if producto >= 10:
            total_suma += (producto // 10) + (producto % 10)
        else:
            total_suma += producto
            
    # Si es múltiplo de 10, la cédula es matemáticamente válida
    return total_suma % 10 == 0


# ================================================================================
#  CÓDIGO DE CLIENTES 
# ================================================================================

# 🔌 REGISTRO DEL BLUEPRINT DE CLIENTES
from routes.clientes import clientes_bp
app.register_blueprint(clientes_bp)

# ====================================================================================
#  CRUD:  EMPLEADOS
# ====================================================================================

@app.route('/empleados')
def listar_empleados():

    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    try:
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        if filtro == 'todos':
            cursor.execute("SELECT id_empleado, nombre, cedula, tanda_labor, porciento_comision, fecha_ingreso, estado FROM empleados ORDER BY id_empleado ASC")
        else:
            cursor.execute("SELECT id_empleado, nombre, cedula, tanda_labor, porciento_comision, fecha_ingreso, estado FROM empleados WHERE estado = 'Activo' ORDER BY id_empleado ASC")
            
        empleados = cursor.fetchall()
        cursor.close()
        return render_template('empleados.html', lista_empleados=empleados, filtro_actual=filtro)
    except Exception as e:
        flash(f"Error al cargar empleados: {str(e)}", "danger")
        return render_template('empleados.html', lista_empleados=[], filtro_actual='activos')

@app.route('/guardar_empleado', methods=['POST'])
def guardar_empleado():
    nombre = request.form.get('txt_nombre', '').strip()
    cedula = request.form.get('txt_cedula', '').strip()
    tanda = request.form.get('sel_tanda', 'Matutina')
    comision = request.form.get('txt_comision', '0').strip()
    fecha_ingreso = request.form.get('txt_fecha_ingreso', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    
    if not nombre or not cedula or not comision or not fecha_ingreso:
        flash("Todos los campos obligatorios del empleado deben ser completados.", "warning")
        return redirect(url_for('listar_empleados'))
        
    #  VALIDADOR JCE
    if not validar_cedula_dominicana(cedula):
        flash(f"Error: La cédula '{cedula}' no es válida para registrar un empleado.", "danger")
        return redirect(url_for('listar_empleados'))
        
    try:
        cursor = mysql.connection.cursor()
        
        #  CÉDULA ÚNICA
        cursor.execute("SELECT id_empleado FROM empleados WHERE cedula = %s", (cedula,))
        if cursor.fetchone():
            cursor.close()
            flash(f"Error: La cédula '{cedula}' ya pertenece a un empleado existente.", "danger")
            return redirect(url_for('listar_empleados'))
            
        cursor.execute("""
            INSERT INTO empleados (nombre, cedula, tanda_labor, porciento_comision, fecha_ingreso, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, cedula, tanda, comision, fecha_ingreso, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Empleado '{nombre}' contratado exitosamente en el sistema.", "success")
    except Exception as e:
        flash(f"Error al guardar empleado: {str(e)}", "danger")
    return redirect(url_for('listar_empleados'))

@app.route('/editar_empleado/<int:id_empleado>', methods=['POST'])
def editar_empleado(id_empleado):
    nombre = request.form.get('txt_nombre_edit', '').strip()
    cedula = request.form.get('txt_cedula_edit', '').strip()
    tanda = request.form.get('sel_tanda_edit', 'Matutina')
    comision = request.form.get('txt_comision_edit', '0').strip()
    fecha_ingreso = request.form.get('txt_fecha_ingreso_edit', '').strip()
    
    if not nombre or not cedula or not comision or not fecha_ingreso:
        flash("Campos vacíos detectados al intentar actualizar el perfil.", "warning")
        return redirect(url_for('listar_empleados'))
        
    #  VALIDADOR JCE EN EDICIÓN
    if not validar_cedula_dominicana(cedula):
        flash(f"Error: La cédula '{cedula}' no es válida.", "danger")
        return redirect(url_for('listar_empleados'))
        
    try:
        cursor = mysql.connection.cursor()
        
        #  CÉDULA ÚNICA EN EDICIÓN
        cursor.execute("SELECT id_empleado FROM empleados WHERE cedula = %s AND id_empleado != %s", (cedula, id_empleado))
        if cursor.fetchone():
            cursor.close()
            flash(f"Error: La cédula '{cedula}' ya está asignada a otro miembro del personal.", "danger")
            return redirect(url_for('listar_empleados'))
            
        cursor.execute("""
            UPDATE empleados 
            SET nombre = %s, cedula = %s, tanda_labor = %s, porciento_comision = %s, fecha_ingreso = %s 
            WHERE id_empleado = %s
        """, (nombre, cedula, tanda, comision, fecha_ingreso, id_empleado))
        mysql.connection.commit()
        cursor.close()
        flash("Expediente del empleado actualizado correctamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar empleado: {str(e)}", "danger")
    return redirect(url_for('listar_empleados'))

@app.route('/cambiar_estado_empleado/<int:id_empleado>/<string:nuevo_estado>')
def cambiar_estado_empleado(id_empleado, nuevo_estado):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE empleados SET estado = %s WHERE id_empleado = %s", (nuevo_estado, id_empleado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado laboral modificado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al alternar estado del empleado: {str(e)}", "danger")
    return redirect(url_for('listar_empleados'))

# ====================================================================================
#  CRUD: TIPOS DE VEHÍCULOS
# ====================================================================================

@app.route('/tipos_vehiculos')
def listar_tipos_vehiculos():

    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
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


@app.route('/editar_tipo_vehiculo/<int:id_tipo>', methods=['POST'])
def editar_tipo_vehiculo(id_tipo):
    nuevo_nombre = request.form.get('txt_descripcion_edit', '').strip()
    if not nuevo_nombre:
        flash("La descripción del tipo de vehículo no puede estar vacía.", "warning")
        return redirect(url_for('listar_tipos_vehiculos'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE tipos_vehiculos SET descripcion = %s WHERE id_tipo_vehiculo = %s", (nuevo_nombre, id_tipo))
        mysql.connection.commit()
        cursor.close()
        flash("Tipo de vehículo renombrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar el tipo de vehículo: {str(e)}", "danger")
    return redirect(url_for('listar_tipos_vehiculos'))


# ===================================
#  CRUD: MARCAS 
# ===================================

@app.route('/marcas')
def listar_marcas():

    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
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

@app.route('/editar_marca/<int:id_marca>', methods=['POST'])
def editar_marca(id_marca):
    nuevo_nombre = request.form.get('txt_descripcion_edit', '').strip()
    
    if not nuevo_nombre:
        flash("La descripción de la marca no puede estar vacía.", "warning")
        return redirect(url_for('listar_marcas'))
        
    try:
        cursor = mysql.connection.cursor()
        # Modificamos únicamente la columna descripción
        cursor.execute("""
            UPDATE marcas 
            SET descripcion = %s 
            WHERE id_marca = %s
        """, (nuevo_nombre, id_marca))
        
        mysql.connection.commit()
        cursor.close()
        flash("Marca renombrada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar el nombre de la marca: {str(e)}", "danger")
        
    return redirect(url_for('listar_marcas'))

# ==================================
#  CRUD: MODELOS 
# ==================================

@app.route('/modelos')
def listar_modelos():

    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    
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

@app.route('/editar_modelo/<int:id_modelo>', methods=['POST'])
def editar_modelo(id_modelo):
    nuevo_nombre = request.form.get('txt_descripcion_edit', '').strip()
    if not nuevo_nombre:
        flash("La descripción del modelo no puede estar vacía.", "warning")
        return redirect(url_for('listar_modelos'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE modelos SET descripcion = %s WHERE id_modelo = %s", (nuevo_nombre, id_modelo))
        mysql.connection.commit()
        cursor.close()
        flash("Modelo renombrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar el modelo: {str(e)}", "danger")
    return redirect(url_for('listar_modelos'))


# ==========================================
#  CRUD: TIPOS DE COMBUSTIBLE 
# ==========================================

@app.route('/tipos_combustible')
def listar_combustibles():

    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    
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

@app.route('/editar_combustible/<int:id_combustible>', methods=['POST'])
def editar_combustible(id_combustible):
    nuevo_nombre = request.form.get('txt_descripcion_edit', '').strip()
    if not nuevo_nombre:
        flash("La descripción del combustible no puede estar vacía.", "warning")
        return redirect(url_for('listar_combustibles'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE tipos_combustible SET descripcion = %s WHERE id_combustible = %s", (nuevo_nombre, id_combustible))
        mysql.connection.commit()
        cursor.close()
        flash("Tipo de combustible renombrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar el tipo de combustible: {str(e)}", "danger")
    return redirect(url_for('listar_combustibles'))

# ==========================================
#  CRUD: VEHÍCULOS 
# ==========================================

@app.route('/vehiculos')
def listar_vehiculos():

    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    
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
                v.estado,
                v.id_marca, v.id_modelo, v.id_tipo_vehiculo, v.id_combustible
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
            
        # Si no existe, procede con la inserción normal
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


@app.route('/editar_vehiculo/<int:id_vehiculo>', methods=['POST'])
def editar_vehiculo(id_vehiculo):
    descripcion = request.form.get('txt_descripcion_edit', '').strip()
    chasis = request.form.get('txt_chasis_edit', '').strip()
    motor = request.form.get('txt_motor_edit', '').strip()
    placa = request.form.get('txt_placa_edit', '').strip()
    
    id_marca = request.form.get('sel_marca_edit')
    id_modelo = request.form.get('sel_modelo_edit')
    id_tipo = request.form.get('sel_tipo_edit')
    id_combustible = request.form.get('sel_combustible_edit')
    
    if not descripcion or not chasis or not motor or not placa or not id_marca or not id_modelo or not id_tipo or not id_combustible:
        flash("Todos los campos son obligatorios al editar el vehículo.", "warning")
        return redirect(url_for('listar_vehiculos'))
        
    try:
        cursor = mysql.connection.cursor()
        
        #  VALIDACIÓN DE PLACA ÚNICA (Excluyendo este mismo vehículo)
        cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE no_placa = %s AND id_vehiculo != %s", (placa, id_vehiculo))
        placa_existente = cursor.fetchone()
        
        if placa_existente:
            cursor.close()
            flash(f"Error: La placa '{placa}' ya está registrada en otro vehículo.", "danger")
            return redirect(url_for('listar_vehiculos'))
            
        # Ejecuta el UPDATE con todos los campos modificados
        cursor.execute("""
            UPDATE vehiculos 
            SET descripcion = %s, no_chasis = %s, no_motor = %s, no_placa = %s, 
                id_tipo_vehiculo = %s, id_marca = %s, id_modelo = %s, id_combustible = %s
            WHERE id_vehiculo = %s
        """, (descripcion, chasis, motor, placa, id_tipo, id_marca, id_modelo, id_combustible, id_vehiculo))
        
        mysql.connection.commit()
        cursor.close()
        flash("Datos del vehículo actualizados correctamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar el vehículo: {str(e)}", "danger")
        
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

# ==========================================
#  CRUD: PROCESO DE INSPECCIÓN
# ==========================================

@app.route('/inspecciones')
def listar_inspecciones():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    try:
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        # Trae las inspecciones cruzando datos con las otras tablas usando  nombres exactos
        query_base = """
            SELECT 
                i.id_inspeccion, i.tiene_ralladuras, i.cantidad_combustible, 
                i.tiene_goma_repuesta, i.tiene_gato, i.tiene_roturas_cristal, 
                i.goma_delantera_izq, i.goma_delantera_der, i.goma_trasera_izq, i.goma_trasera_der,
                i.fecha, i.estado,
                v.descripcion AS vehiculo_nombre,
                c.nombre AS cliente_nombre,
                e.nombre AS empleado_nombre
            FROM inspecciones i
            INNER JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            INNER JOIN clientes c ON i.id_cliente = c.id_cliente
            INNER JOIN empleados e ON i.id_empleado_inspeccion = e.id_empleado
        """
        
        if filtro == 'todos':
            cursor.execute(query_base + " ORDER BY i.id_inspeccion DESC")
        else:
            cursor.execute(query_base + " WHERE i.estado = 'Activo' ORDER BY i.id_inspeccion DESC")
            
        inspecciones = cursor.fetchall()
        
        #  Trae catálogos activos para los dropdowns del formulario de registro
        cursor.execute("SELECT id_vehiculo, descripcion FROM vehiculos WHERE estado = 'Activo'")
        vehiculos_list = cursor.fetchall()
        
        cursor.execute("SELECT id_cliente, nombre FROM clientes WHERE estado = 'Activo'")
        clientes_list = cursor.fetchall()
        
        cursor.execute("SELECT id_empleado, nombre FROM empleados WHERE estado = 'Activo'")
        empleados_list = cursor.fetchall()
        
        cursor.close()
        return render_template('inspecciones.html', 
                               lista_inspecciones=inspecciones, 
                               vehiculos=vehiculos_list, 
                               clientes=clientes_list, 
                               empleados=empleados_list, 
                               filtro_actual=filtro)
    except Exception as e:
        flash(f"Error al cargar inspecciones: {str(e)}", "danger")
        return render_template('inspecciones.html', lista_inspecciones=[], filtro_actual='activos')

@app.route('/guardar_inspeccion', methods=['POST'])
def guardar_inspeccion():
    id_vehiculo = request.form.get('sel_vehiculo')
    id_cliente = request.form.get('sel_cliente')
    id_empleado = request.form.get('sel_empleado')
    fecha = request.form.get('txt_fecha')
    cantidad_combustible = request.form.get('sel_combustible')
    
    # Aqui todo es VARCHAR, por lo que se valida con ternarios para convertir a 'Sí' o 'No' según el checkbox
    tiene_ralladuras = 'Sí' if request.form.get('chk_ralladuras') else 'No'
    tiene_goma_repuesta = 'Sí' if request.form.get('chk_goma') else 'No'
    tiene_gato = 'Sí' if request.form.get('chk_gato') else 'No'
    tiene_roturas_cristal = 'Sí' if request.form.get('chk_cristal') else 'No'
    
    # Estado de las gomas
    g_del_izq = 'Sí' if request.form.get('chk_goma_del_izq') else 'No'
    g_del_der = 'Sí' if request.form.get('chk_goma_del_der') else 'No'
    g_tra_izq = 'Sí' if request.form.get('chk_goma_tra_izq') else 'No'
    g_tra_der = 'Sí' if request.form.get('chk_goma_tra_der') else 'No'
    
    if not id_vehiculo or not id_cliente or not id_empleado or not fecha or not cantidad_combustible:
        flash("Todos los selectores y la fecha son obligatorios.", "warning")
        return redirect(url_for('listar_inspecciones'))
        
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO inspecciones (
                id_vehiculo, id_cliente, id_empleado_inspeccion, fecha, cantidad_combustible,
                tiene_ralladuras, tiene_goma_repuesta, tiene_gato, tiene_roturas_cristal,
                goma_delantera_izq, goma_delantera_der, goma_trasera_izq, goma_trasera_der, estado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Activo')
        """, (id_vehiculo, id_cliente, id_empleado, fecha, cantidad_combustible,
              tiene_ralladuras, tiene_goma_repuesta, tiene_gato, tiene_roturas_cristal,
              g_del_izq, g_del_der, g_tra_izq, g_tra_der))
        mysql.connection.commit()
        cursor.close()
        flash("Hoja de inspección guardada con el reporte de neumáticos completo.", "success")
    except Exception as e:
        flash(f"Error técnico al insertar inspección: {str(e)}", "danger")
        
    return redirect(url_for('listar_inspecciones'))

@app.route('/cambiar_estado_inspeccion/<int:id_inspeccion>/<string:nuevo_estado>')
def cambiar_estado_inspeccion(id_inspeccion, nuevo_estado):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE inspecciones SET estado = %s WHERE id_inspeccion = %s", (nuevo_estado, id_inspeccion))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado de la inspección cambiado a '{nuevo_estado}'.", "success")
    except Exception as e:
        flash(f"Error al anular la inspección: {str(e)}", "danger")
    return redirect(url_for('listar_inspecciones'))

# =================================================================
# 🚗 MÓDULO 9: GESTIÓN DE RENTAS Y DEVOLUCIONES (COMPLETO)
# =================================================================
from datetime import datetime

@app.route('/rentas')
def listar_rentas():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    try:
        cursor = mysql.connection.cursor()
        
        # 1. Traemos el historial de rentas uniendo los catálogos para ver Nombres en vez de IDs
        query = """
            SELECT r.no_renta, CONCAT(v.no_placa, ' - ', m.descripcion, ' ', md.descripcion) AS vehiculo, 
                   c.nombre AS cliente, e.nombre AS empleado, r.fecha_renta, r.fecha_devolucion, 
                   r.monto_x_dia, r.cantidad_dias, r.monto_total, r.estado,
                   r.id_vehiculo, r.id_cliente, r.id_empleado, r.comentario
            FROM rentas r
            JOIN empleados e ON r.id_empleado = e.id_empleado
            JOIN vehiculos v ON r.id_vehiculo = v.id_vehiculo
            JOIN marcas m ON v.id_marca = m.id_marca
            JOIN modelos md ON v.id_modelo = md.id_modelo
            JOIN clientes c ON r.id_cliente = c.id_cliente
            ORDER BY r.no_renta DESC
        """
        cursor.execute(query)
        rentas = cursor.fetchall()

        # Alimenta  los selectores desplegables de los Modales (Crear y Editar)
        cursor.execute("SELECT id_vehiculo, CONCAT(no_placa, ' - ', descripcion) AS descripcion FROM vehiculos "
                       "WHERE estado = 'Activo' "
                       "AND id_vehiculo NOT IN (SELECT id_vehiculo FROM rentas WHERE estado = 'Activo')")
        vehiculos = cursor.fetchall()
        
        cursor.execute("SELECT id_cliente, nombre FROM clientes WHERE estado = 'Activo'")
        clientes = cursor.fetchall()
        
        cursor.execute("SELECT id_empleado, nombre FROM empleados WHERE estado = 'Activo'")
        empleados = cursor.fetchall()
        
        cursor.close()

        return render_template('rentas.html', 
                               lista_rentas=rentas, 
                               lista_vehiculos=vehiculos, 
                               lista_clientes=clientes, 
                               lista_empleados=empleados)
    except Exception as e:
        flash(f"Error al cargar el módulo de rentas: {str(e)}", "danger")
        return render_template('rentas.html', lista_rentas=[], lista_vehiculos=[], lista_clientes=[], lista_empleados=[])


@app.route('/guardar_renta', methods=['POST'])
def guardar_renta():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    id_vehiculo = request.form.get('sel_vehiculo')
    id_cliente = request.form.get('sel_cliente')
    id_empleado = request.form.get('sel_empleado')
    fecha_renta_str = request.form.get('txt_fecha_renta')
    fecha_devolucion_str = request.form.get('txt_fecha_devolucion') # Fecha estipulada sugerida
    monto_x_dia = request.form.get('txt_monto_x_dia')
    comentario = request.form.get('txt_comentario', '').strip()

    try:
        cursor = mysql.connection.cursor()

        # Validamos servidor-side que el vehículo no tenga otra renta activa abierta
        cursor.execute("SELECT COUNT(*) AS cantidad FROM rentas WHERE id_vehiculo = %s AND estado = 'Activo'", (id_vehiculo,))
        activo = cursor.fetchone()
        cantidad_activa = activo['cantidad'] if isinstance(activo, dict) else activo[0]
        if cantidad_activa > 0:
            flash("El vehículo seleccionado ya está en renta y no ha sido devuelto.", "danger")
            cursor.close()
            return redirect(url_for('listar_rentas'))

        # El contrato nace estrictamente en 'Activo' con cantidad_dias = 0 y monto_total = 0.00
        query = """
            INSERT INTO rentas (id_vehiculo, id_cliente, id_empleado, fecha_renta, fecha_devolucion, monto_x_dia, cantidad_dias, monto_total, estado, comentario)
            VALUES (%s, %s, %s, %s, %s, %s, 0, 0.00, 'Activo', %s)
        """
        cursor.execute(query, (id_vehiculo, id_cliente, id_empleado, fecha_renta_str, fecha_devolucion_str, monto_x_dia, comentario))
        mysql.connection.commit()
        cursor.close()
        flash("Contrato de renta generado exitosamente (Estado: Activo)", "success")
    except Exception as e:
        flash(f"Error al procesar la salida del vehículo: {str(e)}", "danger")
        
    return redirect(url_for('listar_rentas'))


@app.route('/editar_renta_activa', methods=['POST'])
def editar_renta_activa():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    no_renta = request.form.get('txt_no_renta')
    id_vehiculo = request.form.get('sel_vehiculo')
    id_cliente = request.form.get('sel_cliente')
    id_empleado = request.form.get('sel_empleado')
    fecha_renta_str = request.form.get('txt_fecha_renta')
    fecha_devolucion_str = request.form.get('txt_fecha_devolucion')
    monto_x_dia = request.form.get('txt_monto_x_dia')
    comentario = request.form.get('txt_comentario', '').strip()

    try:
        cursor = mysql.connection.cursor()
        # Modifica el contrato guardando los cambios erróneos y lo mantiene vivo en estado 'Activo'
        query = """
            UPDATE rentas 
            SET id_vehiculo = %s, id_cliente = %s, id_empleado = %s, 
                fecha_renta = %s, fecha_devolucion = %s, monto_x_dia = %s, comentario = %s
            WHERE no_renta = %s
        """
        cursor.execute(query, (id_vehiculo, id_cliente, id_empleado, fecha_renta_str, fecha_devolucion_str, monto_x_dia, comentario, no_renta))
        mysql.connection.commit()
        cursor.close()
        flash("Contrato de renta corregido con éxito", "success")
    except Exception as e:
        flash(f"Error al modificar el contrato: {str(e)}", "danger")
        
    return redirect(url_for('listar_rentas'))


@app.route('/marcar_devolucion', methods=['POST'])
def marcar_devolucion():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    no_renta = request.form.get('txt_no_renta')
    fecha_devolucion_str = request.form.get('txt_fecha_devolucion') # Fecha real que pones en el modal

    try:
        cursor = mysql.connection.cursor()
        # Busca la fecha de salida guardada al inicio y la tarifa pactada
        cursor.execute("SELECT fecha_renta, monto_x_dia FROM rentas WHERE no_renta = %s", (no_renta,))
        renta = cursor.fetchone()

        if not renta:
            flash("No se encontró el registro de renta.", "danger")
            return redirect(url_for('listar_rentas'))

        f_renta_origen = renta['fecha_renta'] if isinstance(renta, dict) else renta[0]
        monto_diario = float(renta['monto_x_dia'] if isinstance(renta, dict) else renta[1])

        # Convertimos a objetos tipo fecha de Python para restar días
        f_dev = datetime.strptime(fecha_devolucion_str, '%Y-%m-%d').date()
        if isinstance(f_renta_origen, str):
            f_renta = datetime.strptime(f_renta_origen, '%Y-%m-%d').date()
        elif isinstance(f_renta_origen, datetime):
            f_renta = f_renta_origen.date()
        else:
            f_renta = f_renta_origen

        # Cálculo de días y multiplicación automática
        dias = (f_dev - f_renta).days
        if dias <= 0:
            dias = 1
            
        total_pesos = dias * monto_diario

        # Cerramos permanentemente el contrato pasando el estado a 'Devuelto'
        query_update = """
            UPDATE rentas 
            SET fecha_devolucion = %s, cantidad_dias = %s, monto_total = %s, estado = 'Devuelto'
            WHERE no_renta = %s
        """
        cursor.execute(query_update, (fecha_devolucion_str, dias, total_pesos, no_renta))
        mysql.connection.commit()
        cursor.close()
        
        flash(f"¡Vehículo recibido! Días calculados: {dias} | Monto Total: RD$ {total_pesos:,.2f}", "success")
    except Exception as e:
        flash(f"Error interno al procesar la devolución: {str(e)}", "danger")
        
    return redirect(url_for('listar_rentas'))

# ======================
#   CIERRE  DEL ARCHIVO
# =======================
if __name__ == '__main__':
    app.run(debug=True)
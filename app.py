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

#  REGISTRO DEL BLUEPRINT DE CLIENTES
from routes.clientes import clientes_bp
app.register_blueprint(clientes_bp)

# ====================================================================================
#  CRUD:  EMPLEADOS
# ====================================================================================

#  REGISTRO DEL BLUEPRINT DE EMPLEADOS
from routes.empleados import empleados_bp
app.register_blueprint(empleados_bp)

# ====================================================================================
#  CRUD: TIPOS DE VEHÍCULOS
# ====================================================================================

from routes.tipos_vehiculos import tipos_vehiculos_bp
app.register_blueprint(tipos_vehiculos_bp)


# ===================================
#  CRUD: MARCAS 
# ===================================

#  REGISTRO DEL BLUEPRINT DE MARCAS
from routes.marcas import marcas_bp
app.register_blueprint(marcas_bp)

# ==================================
#  CRUD: MODELOS 
# ==================================

#  REGISTRO DEL BLUEPRINT DE MODELOS
from routes.modelos import modelos_bp
app.register_blueprint(modelos_bp)

# ==========================================
#  CRUD: TIPOS DE COMBUSTIBLE 
# ==========================================

# REGISTRO DEL BLUEPRINT DE TIPOS DE COMBUSTIBLE
from routes.tipos_combustible import tipos_combustible_bp
app.register_blueprint(tipos_combustible_bp)

# ==========================================
#  CRUD: VEHÍCULOS 
# ==========================================
from routes.vehiculos import vehiculos_bp
app.register_blueprint(vehiculos_bp)

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
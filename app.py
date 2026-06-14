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

from routes.inspecciones import inspecciones_bp
app.register_blueprint(inspecciones_bp)

# =================================================================
#  MÓDULO 9: GESTIÓN DE RENTAS Y DEVOLUCIONES 
# =================================================================

from routes.rentas import rentas_bp
app.register_blueprint(rentas_bp)



# =================================================================
#  MÓDULO 10: CONSULTAS DINÁMICAS Y REPORTES
# =================================================================
# REGISTRO DEL BLUEPRINT DE CONSULTAS POR CRITERIOS
from routes.consultas import consultas_bp
app.register_blueprint(consultas_bp)

# ======================
#   CIERRE  DEL ARCHIVO
# =======================
if __name__ == '__main__':
    app.run(debug=True)
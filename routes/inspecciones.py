from flask import Blueprint, render_template, request, redirect, url_for, flash, session

#  Blueprint para Inspecciones
inspecciones_bp = Blueprint('inspecciones', __name__)

@inspecciones_bp.route('/inspecciones')
def listar_inspecciones():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    try:
        #  Importación local segura
        from app import mysql
        
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        # Trae las inspecciones cruzando datos con las otras tablas usando nombres exactos
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
        
        # Trae catálogos activos para los dropdowns del formulario de registro
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


@inspecciones_bp.route('/guardar_inspeccion', methods=['POST'])
def guardar_inspeccion():
    #  Importación local segura
    from app import mysql
    
    id_vehiculo = request.form.get('sel_vehiculo')
    id_cliente = request.form.get('sel_cliente')
    id_empleado = request.form.get('sel_empleado')
    fecha = request.form.get('txt_fecha')
    cantidad_combustible = request.form.get('sel_combustible')
    
    # Aquí todo es VARCHAR, por lo que se valida con ternarios para convertir a 'Sí' o 'No' según el checkbox
    tiene_ralladuras = 'Sí' if request.form.get('chk_ralladuras') else 'No'
    tiene_goma_repuesta = 'Sí' if request.form.get('chk_goma') else 'No'
    tiene_gato = 'Sí' if request.form.get('chk_gato') else 'No'
    tiene_roturas_cristal = 'Sí' if request.form.get('chk_cristal') else 'No'
    
    # Estado de las gomas
    g_del_izq = 'Sí' if request.form.get('chk_goma_del_izq') else 'No'
    g_del_der = 'Sí' if request.form.get('chk_goma_del_der') else 'No'
    g_tra_izq = 'Sí' if request.form.get('chk_goma_tra_izq') else 'No'
    g_tra_der = 'Sí' if request.form.get('chk_goma_tra_der') else 'No'
    
    #  VALIDACIÓN CORREGIDA Y LIMPIA:
    if not id_vehiculo or not id_cliente or not id_empleado or not fecha or not cantidad_combustible:
        flash("Todos los selectores y la fecha son obligatorios.", "warning")
        return redirect(url_for('inspecciones.listar_inspecciones'))
        
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
        
    return redirect(url_for('inspecciones.listar_inspecciones'))
        
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
        
    return redirect(url_for('inspecciones.listar_inspecciones'))


@inspecciones_bp.route('/cambiar_estado_inspeccion/<int:id_inspeccion>/<string:nuevo_estado>')
def cambiar_estado_inspeccion(id_inspeccion, nuevo_estado):
    try:
        # Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE inspecciones SET estado = %s WHERE id_inspeccion = %s", (nuevo_estado, id_inspeccion))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado de la inspección cambiado a '{nuevo_estado}'.", "success")
    except Exception as e:
        flash(f"Error al anular la inspección: {str(e)}", "danger")
        
    return redirect(url_for('inspecciones.listar_inspecciones'))
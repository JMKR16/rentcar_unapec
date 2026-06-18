from flask import Blueprint, render_template, request, redirect, url_for, flash, session

#  Crea el Blueprint para Empleados
empleados_bp = Blueprint('empleados', __name__)

@empleados_bp.route('/empleados')
def listar_empleados():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    try:
        #  Importación local segura
        from app import mysql
        
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


@empleados_bp.route('/guardar_empleado', methods=['POST'])
def guardar_empleado():
    # Importación local segura
    from app import mysql, validar_cedula_dominicana
    
    nombre = request.form.get('txt_nombre', '').strip()
    cedula = request.form.get('txt_cedula', '').strip()
    tanda = request.form.get('sel_tanda', 'Matutina')
    comision = request.form.get('txt_comision', '0').strip()
    fecha_ingreso = request.form.get('txt_fecha_ingreso', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    
    if not nombre or not cedula or not comision or not fecha_ingreso:
        flash("Todos los campos obligatorios del empleado deben ser completados.", "warning")
        return redirect(url_for('empleados.listar_empleados'))
        
    # VALIDADOR JCE
    if not validar_cedula_dominicana(cedula):
        flash(f"Error: La cédula '{cedula}' no es válida para registrar un empleado.", "danger")
        return redirect(url_for('empleados.listar_empleados'))
        
    try:
        cursor = mysql.connection.cursor()
        
        # CÉDULA ÚNICA
        cursor.execute("SELECT id_empleado FROM empleados WHERE cedula = %s", (cedula,))
        if cursor.fetchone():
            cursor.close()
            flash(f"Error: La cédula '{cedula}' ya pertenece a un empleado existente.", "danger")
            return redirect(url_for('empleados.listar_empleados'))
            
        cursor.execute("""
            INSERT INTO empleados (nombre, cedula, tanda_labor, porciento_comision, fecha_ingreso, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, cedula, tanda, comision, fecha_ingreso, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Empleado '{nombre}' contratado exitosamente en el sistema.", "success")
    except Exception as e:
        flash(f"Error al guardar empleado: {str(e)}", "danger")
        
    return redirect(url_for('empleados.listar_empleados'))


@empleados_bp.route('/editar_empleado/<int:id_empleado>', methods=['POST'])
def editar_empleado(id_empleado):
    # Importación local segura
    from app import mysql, validar_cedula_dominicana
    
    nombre = request.form.get('txt_nombre_edit', '').strip()
    cedula = request.form.get('txt_cedula_edit', '').strip()
    tanda = request.form.get('sel_tanda_edit', 'Matutina')
    comision = request.form.get('txt_comision_edit', '0').strip()
    fecha_ingreso = request.form.get('txt_fecha_ingreso_edit', '').strip()
    
    if not nombre or not cedula or not comision or not fecha_ingreso:
        flash("Campos vacíos detectados al intentar actualizar el perfil.", "warning")
        return redirect(url_for('empleados.listar_empleados'))
        
    # VALIDADOR JCE EN EDICIÓN
    if not validar_cedula_dominicana(cedula):
        flash(f"Error: La cédula '{cedula}' no es válida.", "danger")
        return redirect(url_for('empleados.listar_empleados'))
        
    try:
        cursor = mysql.connection.cursor()
        
        # CÉDULA ÚNICA EN EDICIÓN
        cursor.execute("SELECT id_empleado FROM empleados WHERE cedula = %s AND id_empleado != %s", (cedula, id_empleado))
        if cursor.fetchone():
            cursor.close()
            flash(f"Error: La cédula '{cedula}' ya está asignada a otro miembro del personal.", "danger")
            return redirect(url_for('empleados.listar_empleados'))
            
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
        
    return redirect(url_for('empleados.listar_empleados'))


@empleados_bp.route('/cambiar_estado_empleado/<int:id_empleado>/<string:nuevo_estado>')
def cambiar_estado_empleado(id_empleado, nuevo_estado):
    try:
        #  Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE empleados SET estado = %s WHERE id_empleado = %s", (nuevo_estado, id_empleado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado laboral modificado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al alternar estado del empleado: {str(e)}", "danger")
        
    return redirect(url_for('empleados.listar_empleados'))


#  BORRADO FÍSICO SEGURO CON COMPROBACIÓN HISTÓRICA COMPLETA DE EMPLEADOS
@empleados_bp.route('/eliminar_empleado/<int:id_empleado>')
def eliminar_empleado(id_empleado):
    try:
        from app import mysql
        cursor = mysql.connection.cursor()
        
        # ESCANEO TOTAL: Busca si el empleado firmó rentas o auditó inspecciones
        query_verificar = """
            SELECT 
                (SELECT COUNT(*) FROM rentas WHERE id_empleado = %s) AS en_rentas,
                (SELECT COUNT(*) FROM inspecciones WHERE id_empleado_inspeccion = %s) AS en_inspecciones
        """
        cursor.execute(query_verificar, (id_empleado, id_empleado))
        resultado = cursor.fetchone()
        
        # Extracción segura para diccionarios o tuplas
        ren = resultado['en_rentas'] if isinstance(resultado, dict) else resultado[0]
        insp = resultado['en_inspecciones'] if isinstance(resultado, dict) else resultado[1]
        
        # Si tiene cualquier registro operativo, congela la eliminación física inmediatamente
        if ren > 0 or insp > 0:
            cursor.close()
            flash(" Operación denegada: No se puede eliminar este empleado porque figura como responsable registrado de transacciones históricas (contratos de renta o auditorías de inspección).", "danger")
            return redirect(url_for('empleados.listar_empleados'))
            
        # Si está completamente libre de dependencias, procedemos a borrar físicamente
        cursor.execute("DELETE FROM empleados WHERE id_empleado = %s", (id_empleado,))
        mysql.connection.commit()
        cursor.close()
        
        flash("El expediente del empleado ha sido removido físicamente de la base de datos de forma segura.", "success")
    except Exception as e:
        flash(f"Error de restricción de integridad relacional al intentar eliminar el empleado: {str(e)}", "danger")
        
    return redirect(url_for('empleados.listar_empleados'))
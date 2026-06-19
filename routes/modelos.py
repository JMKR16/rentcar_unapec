from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# Blueprint para Modelos
modelos_bp = Blueprint('modelos', __name__)

@modelos_bp.route('/modelos')
def listar_modelos():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    
    try:
        # Importación local segura
        from app import mysql
        
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


@modelos_bp.route('/guardar_modelo', methods=['POST'])
def guardar_modelo():
    #  Importación local segura
    from app import mysql
    
    id_marca = request.form.get('sel_marca')
    nombre_modelo = request.form.get('txt_modelo', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    
    if not id_marca or not nombre_modelo:
        flash("Todos los campos son obligatorios.", "warning")
        return redirect(url_for('modelos.listar_modelos'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO modelos (id_marca, descripcion, estado) VALUES (%s, %s, %s)", (id_marca, nombre_modelo, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Modelo '{nombre_modelo}' registered con éxito.", "success")
    except Exception as e:
        flash(f"Error al guardar modelo: {str(e)}", "danger")
        
    return redirect(url_for('modelos.listar_modelos'))


@modelos_bp.route('/cambiar_estado_modelo/<int:id_modelo>/<string:nuevo_estado>')
def cambiar_estado_modelo(id_modelo, nuevo_estado):
    try:
        # Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        
        #  Si se intenta ACTIVAR el modelo, valida que su marca principal esté activa
        if nuevo_estado == 'Activo':
            query_verificar_marca = """
                SELECT m.estado AS estado_marca, m.descripcion AS nombre_marca
                FROM modelos mo
                INNER JOIN marcas m ON mo.id_marca = m.id_marca
                WHERE mo.id_modelo = %s
            """
            cursor.execute(query_verificar_marca, (id_modelo,))
            resultado = cursor.fetchone()
            
            estado_marca = resultado['estado_marca'] if isinstance(resultado, dict) else resultado[0]
            nombre_marca = resultado['nombre_marca'] if isinstance(resultado, dict) else resultado[1]
            
            if estado_marca == 'Inactivo':
                cursor.close()
                flash(f" Operación denegada: No se puede activar este modelo porque su marca principal '{nombre_marca}' se encuentra inactiva.", "danger")
                return redirect(url_for('modelos.listar_modelos'))
        
        #  Actualiza el estado del Modelo seleccionado
        cursor.execute("UPDATE modelos SET estado = %s WHERE id_modelo = %s", (nuevo_estado, id_modelo))
        
        #  Desactiva/Activa todos los vehículos de este modelo específico
        cursor.execute("UPDATE vehiculos SET estado = %s WHERE id_modelo = %s", (nuevo_estado, id_modelo))
        
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del modelo y sus vehículos individuales asociados actualizado a '{nuevo_estado}' con éxito.", "success")
        
    except Exception as e:
        flash(f"Error al cambiar el estado del modelo en cascada: {str(e)}", "danger")
        
    return redirect(url_for('modelos.listar_modelos'))


@modelos_bp.route('/editar_modelo/<int:id_modelo>', methods=['POST'])
def editar_modelo(id_modelo):
    #  Importación local segura
    from app import mysql
    
    nuevo_nombre = request.form.get('txt_descripcion_edit', '').strip()
    if not nuevo_nombre:
        flash("La descripción del modelo no puede estar vacía.", "warning")
        return redirect(url_for('modelos.listar_modelos'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE modelos SET descripcion = %s WHERE id_modelo = %s", (nuevo_nombre, id_modelo))
        mysql.connection.commit()
        cursor.close()
        flash("Modelo renombrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar el modelo: {str(e)}", "danger")
        
    return redirect(url_for('modelos.listar_modelos'))


#  bp.route para eliminar modelo con comprobación de integridad referencial en vehículos, rentas e inspecciones
@modelos_bp.route('/eliminar_modelo/<int:id_modelo>')
def eliminar_modelo(id_modelo):
    try:
        from app import mysql
        cursor = mysql.connection.cursor()
        
        #  Valida si el modelo se usa en vehículos, rentas o inspecciones
        query_verificar_uso = """
            SELECT 
                (SELECT COUNT(*) FROM vehiculos WHERE id_modelo = %s) AS en_vehiculos,
                (SELECT COUNT(*) FROM rentas r JOIN vehiculos v ON r.id_vehiculo = v.id_vehiculo WHERE v.id_modelo = %s) AS en_rentas,
                (SELECT COUNT(*) FROM inspecciones i JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo WHERE v.id_modelo = %s) AS en_inspecciones
        """
        cursor.execute(query_verificar_uso, (id_modelo, id_modelo, id_modelo))
        resultado = cursor.fetchone()
        
        # Controla la extracción de datos por diccionario o tupla según el entorno
        veh = resultado['en_vehiculos'] if isinstance(resultado, dict) else resultado[0]
        ren = resultado['en_rentas'] if isinstance(resultado, dict) else resultado[1]
        insp = resultado['en_inspecciones'] if isinstance(resultado, dict) else resultado[2]
        
        # Si tiene cualquier tipo de dependencia transaccional, bloquea la acción física
        if veh > 0 or ren > 0 or insp > 0:
            cursor.close()
            flash(" Operación denegada: No se puede eliminar este modelo permanentemente porque posee unidades registradas en el inventario o historial operativo.", "danger")
            return redirect(url_for('modelos.listar_modelos'))
            
        # Si el conteo es 0 absoluto, procede a borrar físicamente de forma segura
        cursor.execute("DELETE FROM modelos WHERE id_modelo = %s", (id_modelo,))
        mysql.connection.commit()
        cursor.close()
        
        flash("El modelo ha sido eliminado físicamente del catálogo con éxito.", "success")
    except Exception as e:
        flash(f"Error de restricción de integridad al intentar eliminar el modelo: {str(e)}", "danger")
        
    return redirect(url_for('modelos.listar_modelos'))
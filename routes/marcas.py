from flask import Blueprint, render_template, request, redirect, url_for, flash, session

#  Blueprint para Marcas
marcas_bp = Blueprint('marcas', __name__)

@marcas_bp.route('/marcas')
def listar_marcas():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    try:
        # Importación local segura
        from app import mysql
        
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        if filtro == 'todos':
            cursor.execute("SELECT id_marca, descripcion, estado FROM marcas ORDER BY id_marca ASC")
        else:
            cursor.execute("SELECT id_marca, descripcion, estado FROM marcas WHERE estado = 'Activo' ORDER BY id_marca ASC")
            
        marcas = cursor.fetchall()
        cursor.close()
        
        return render_template('marcas.html', lista_marcas=marcas, filtro_actual=filtro)
    except Exception as e:
        flash(f"Error al cargar marcas: {str(e)}", "danger")
        return render_template('marcas.html', lista_marcas=[], filtro_actual='activos')


@marcas_bp.route('/guardar_marca', methods=['POST'])
def guardar_marca():
    # Importación local segura
    from app import mysql
    
    nombre_marca = request.form.get('txt_marca', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    
    if not nombre_marca:
        flash("El nombre de la marca es obligatorio.", "warning")
        return redirect(url_for('marcas.listar_marcas'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO marcas (descripcion, estado) VALUES (%s, %s)", (nombre_marca, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Marca '{nombre_marca}' registrada exitosamente.", "success")
    except Exception as e:
        flash(f"Error al guardar marca: {str(e)}", "danger")
        
    return redirect(url_for('marcas.listar_marcas'))


@marcas_bp.route('/cambiar_estado_marca/<int:id_marca>/<string:nuevo_estado>')
def cambiar_estado_marca(id_marca, nuevo_estado):
    try:
        #  Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        
        #  Si se intenta INACTIVAR la marca, validamos que no esté en uso
        if nuevo_estado == 'Inactivo':
            query_verificar = """
                SELECT COUNT(r.no_renta) AS rentas_activas
                FROM rentas r
                JOIN vehiculos v ON r.id_vehiculo = v.id_vehiculo
                WHERE v.id_marca = %s AND r.estado = 'Activo'
            """
            cursor.execute(query_verificar, (id_marca,))
            chequeo = cursor.fetchone()
            
            # Controlamos si el cursor devuelve diccionario o tupla según tu configuración
            rentas_activas = chequeo['rentas_activas'] if isinstance(chequeo, dict) else chequeo[0]
            
            # Si hay carros de esa marca corriendo en la calle, bloqueamos la acción de inmediato
            if rentas_activas > 0:
                cursor.close()
                flash(" Operación denegada: No se puede inactivar esta marca porque posee vehículos asociados en rentas vigentes (en uso).", "danger")
                return redirect(url_for('marcas.listar_marcas'))
        
        #  Actualiza el estado de la Marca
        cursor.execute("UPDATE marcas SET estado = %s WHERE id_marca = %s", (nuevo_estado, id_marca))
        
        #  ACTUALIZACIÓN EN CASCADA: Desactiva/Activa todos sus modelos dependientes automáticamente
        cursor.execute("UPDATE modelos SET estado = %s WHERE id_marca = %s", (nuevo_estado, id_marca))
        
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado de la marca y sus modelos dependientes actualizado a '{nuevo_estado}' con éxito.", "success")
        
    except Exception as e:
        flash(f"Error al cambiar el estado de la marca en cascada: {str(e)}", "danger")
        
    return redirect(url_for('marcas.listar_marcas'))


@marcas_bp.route('/editar_marca/<int:id_marca>', methods=['POST'])
def editar_marca(id_marca):
    # Importación local segura
    from app import mysql
    
    nuevo_nombre = request.form.get('txt_descripcion_edit', '').strip()
    
    if not nuevo_nombre:
        flash("La descripción de la marca no puede estar vacía.", "warning")
        return redirect(url_for('marcas.listar_marcas'))
        
    try:
        cursor = mysql.connection.cursor()
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
        
    return redirect(url_for('marcas.listar_marcas'))
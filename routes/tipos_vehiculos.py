from flask import Blueprint, render_template, request, redirect, url_for, flash, session

#  Blueprint para Tipos de Vehículos
tipos_vehiculos_bp = Blueprint('tipos_vehiculos', __name__)

@tipos_vehiculos_bp.route('/tipos_vehiculos')
def listar_tipos_vehiculos():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    try:
        #  Importación local segura
        from app import mysql
        
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


@tipos_vehiculos_bp.route('/guardar_tipo_vehiculo', methods=['POST'])
def guardar_tipo_vehiculo():
    #  Importación local segura
    from app import mysql
    
    descripcion = request.form.get('txt_descripcion', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    
    if not descripcion:
        flash("La descripción es obligatoria.", "warning")
        return redirect(url_for('tipos_vehiculos.listar_tipos_vehiculos'))
        
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO tipos_vehiculos (descripcion, estado) VALUES (%s, %s)", (descripcion, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Tipo '{descripcion}' registrado con éxito.", "success")
    except Exception as e:
        flash(f"Error al guardar tipo: {str(e)}", "danger")
        
    return redirect(url_for('tipos_vehiculos.listar_tipos_vehiculos'))


@tipos_vehiculos_bp.route('/cambiar_estado_tipo/<int:id_tipo>/<string:nuevo_estado>')
def cambiar_estado_tipo(id_tipo, nuevo_estado):
    try:
        # 🟢 Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE tipos_vehiculos SET estado = %s WHERE id_tipo_vehiculo = %s", (nuevo_estado, id_tipo))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del tipo de vehículo actualizado a '{nuevo_estado}'.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        
    return redirect(url_for('tipos_vehiculos.listar_tipos_vehiculos'))


@tipos_vehiculos_bp.route('/editar_tipo_vehiculo/<int:id_tipo>', methods=['POST'])
def editar_tipo_vehiculo(id_tipo):
    # 🟢 Importación local segura
    from app import mysql
    
    nuevo_nombre = request.form.get('txt_descripcion_edit', '').strip()
    if not nuevo_nombre:
        flash("La descripción del tipo de vehículo no puede estar vacía.", "warning")
        return redirect(url_for('tipos_vehiculos.listar_tipos_vehiculos'))
        
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE tipos_vehiculos SET descripcion = %s WHERE id_tipo_vehiculo = %s", (nuevo_nombre, id_tipo))
        mysql.connection.commit()
        cursor.close()
        flash("Tipo de vehículo renombrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar el tipo de vehículo: {str(e)}", "danger")
        
    return redirect(url_for('tipos_vehiculos.listar_tipos_vehiculos'))
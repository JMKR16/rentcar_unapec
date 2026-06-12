from flask import Blueprint, render_template, request, redirect, url_for, flash, session

#  Blueprint para Vehículos
vehiculos_bp = Blueprint('vehiculos', __name__)

@vehiculos_bp.route('/vehiculos')
def listar_vehiculos():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    
    try:
        #  Importación local segura
        from app import mysql
        
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        # Se toman los catálogos protegidos (Solo los que estén ACTIVOS)
        cursor.execute("SELECT id_marca, descripcion FROM marcas WHERE estado = 'Activo' ORDER BY descripcion ASC")
        cat_marcas = cursor.fetchall()
        
        cursor.execute("SELECT id_modelo, descripcion, id_marca FROM modelos WHERE estado = 'Activo'")
        cat_modelos = cursor.fetchall()
        
        cursor.execute("SELECT id_tipo_vehiculo, descripcion FROM tipos_vehiculos WHERE estado = 'Activo' ORDER BY descripcion ASC")
        cat_tipos = cursor.fetchall()
        
        cursor.execute("SELECT id_combustible, descripcion FROM tipos_combustible WHERE estado = 'Activo' ORDER BY descripcion ASC")
        cat_combustibles = cursor.fetchall()
        
        # Se construye el query de la tabla relacional CON INNER JOINS
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
        
        # Filtro de Soft Delete sobre la tabla de vehículos
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


@vehiculos_bp.route('/guardar_vehiculo', methods=['POST'])
def guardar_vehiculo():
    #  Importación local segura
    from app import mysql
    
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
        return redirect(url_for('vehiculos.listar_vehiculos'))
        
    try:
        cursor = mysql.connection.cursor()
        
        # VALIDACIÓN DE PLACA ÚNICA
        cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE no_placa = %s", (placa,))
        placa_existente = cursor.fetchone()
        
        if placa_existente:
            cursor.close()
            flash(f"Error: La placa '{placa}' ya está registrada en el sistema con otro vehículo.", "danger")
            return redirect(url_for('vehiculos.listar_vehiculos'))
            
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
        
    return redirect(url_for('vehiculos.listar_vehiculos'))


@vehiculos_bp.route('/editar_vehiculo/<int:id_vehiculo>', methods=['POST'])
def editar_vehiculo(id_vehiculo):
    # Importación local segura
    from app import mysql
    
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
        return redirect(url_for('vehiculos.listar_vehiculos'))
        
    try:
        cursor = mysql.connection.cursor()
        
        # VALIDACIÓN DE PLACA ÚNICA (Excluyendo este mismo vehículo)
        cursor.execute("SELECT id_vehiculo FROM vehiculos WHERE no_placa = %s AND id_vehiculo != %s", (placa, id_vehiculo))
        placa_existente = cursor.fetchone()
        
        if placa_existente:
            cursor.close()
            flash(f"Error: La placa '{placa}' ya está registrada en otro vehículo.", "danger")
            return redirect(url_for('vehiculos.listar_vehiculos'))
            
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
        
    return redirect(url_for('vehiculos.listar_vehiculos'))


@vehiculos_bp.route('/cambiar_estado_vehiculo/<int:id_vehiculo>/<string:nuevo_estado>')
def cambiar_estado_vehiculo(id_vehiculo, nuevo_estado):
    try:
        # Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE vehiculos SET estado = %s WHERE id_vehiculo = %s", (nuevo_estado, id_vehiculo))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del vehículo ID {id_vehiculo} actualizado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al cambiar el estado del vehículo: {str(e)}", "danger")
        
    return redirect(url_for('vehiculos.listar_vehiculos'))
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
        flash(f"Modelo '{nombre_modelo}' registrado con éxito.", "success")
    except Exception as e:
        flash(f"Error al guardar modelo: {str(e)}", "danger")
        
    return redirect(url_for('modelos.listar_modelos'))


@modelos_bp.route('/cambiar_estado_modelo/<int:id_modelo>/<string:nuevo_estado>')
def cambiar_estado_modelo(id_modelo, nuevo_estado):
    try:
        # 🟢Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE modelos SET estado = %s WHERE id_modelo = %s", (nuevo_estado, id_modelo))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del modelo actualizado a '{nuevo_estado}'.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        
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
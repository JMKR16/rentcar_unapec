from flask import Blueprint, render_template, request, redirect, url_for, flash, session

#  Blueprint para Tipos de Combustible
tipos_combustible_bp = Blueprint('tipos_combustible', __name__)

@tipos_combustible_bp.route('/tipos_combustible')
def listar_combustibles():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión primero.", "danger")
        return redirect(url_for('login'))
    
    try:
        #  Importación local segura
        from app import mysql
        
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


@tipos_combustible_bp.route('/guardar_combustible', methods=['POST'])
def guardar_combustible():
    #  Importación local segura
    from app import mysql
    
    descripcion = request.form.get('txt_descripcion', '').strip()
    estado = request.form.get('sel_estado', 'Activo')
    
    if not descripcion:
        flash("La descripción del combustible es obligatoria.", "warning")
        return redirect(url_for('tipos_combustible.listar_combustibles'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO tipos_combustible (descripcion, estado) VALUES (%s, %s)", (descripcion, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Combustible '{descripcion}' registrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al guardar tipo de combustible: {str(e)}", "danger")
        
    return redirect(url_for('tipos_combustible.listar_combustibles'))


@tipos_combustible_bp.route('/cambiar_estado_combustible/<int:id_combustible>/<string:nuevo_estado>')
def cambiar_estado_combustible(id_combustible, nuevo_estado):
    try:
        #  Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE tipos_combustible SET estado = %s WHERE id_combustible = %s", (nuevo_estado, id_combustible))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del combustible actualizado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al cambiar el estado del combustible: {str(e)}", "danger")
        
    return redirect(url_for('tipos_combustible.listar_combustibles'))


@tipos_combustible_bp.route('/editar_combustible/<int:id_combustible>', methods=['POST'])
def editar_combustible(id_combustible):
    # Importación local segura
    from app import mysql
    
    nuevo_nombre = request.form.get('txt_descripcion_edit', '').strip()
    if not nuevo_nombre:
        flash("La descripción del combustible no puede estar vacía.", "warning")
        return redirect(url_for('tipos_combustible.listar_combustibles'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE tipos_combustible SET descripcion = %s WHERE id_combustible = %s", (nuevo_nombre, id_combustible))
        mysql.connection.commit()
        cursor.close()
        flash("Tipo de combustible renombrado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar el tipo de combustible: {str(e)}", "danger")
        
    return redirect(url_for('tipos_combustible.listar_combustibles'))
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
        cursor.execute("UPDATE marcas SET estado = %s WHERE id_marca = %s", (nuevo_estado, id_marca))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado de la marca actualizado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al cambiar el estado de la marca: {str(e)}", "danger")
        
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
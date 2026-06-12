from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# 🔌 Creamos el Blueprint para Clientes (Sin importaciones globales de app.py aquí arriba)
clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/clientes')
def listar_clientes():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión.", "danger")
        return redirect(url_for('login'))
        
    try:
        # 🟢 Importación local segura
        from app import mysql
        
        filtro = request.args.get('ver', 'activos')
        cursor = mysql.connection.cursor()
        
        if filtro == 'todos':
            cursor.execute("SELECT id_cliente, nombre, cedula, no_tarjeta_cr, limite_credito, tipo_persona, estado FROM clientes ORDER BY id_cliente ASC")
        else:
            cursor.execute("SELECT id_cliente, nombre, cedula, no_tarjeta_cr, limite_credito, tipo_persona, estado FROM clientes WHERE estado = 'Activo' ORDER BY id_cliente ASC")
            
        clientes = cursor.fetchall()
        cursor.close()
        return render_template('clientes.html', lista_clientes=clientes, filtro_actual=filtro)
    except Exception as e:
        flash(f"Error al cargar clientes: {str(e)}", "danger")
        return render_template('clientes.html', lista_clientes=[], filtro_actual='activos')


@clientes_bp.route('/guardar_cliente', methods=['POST'])
def guardar_cliente():
    # 🟢 Importación local segura
    from app import mysql, validar_cedula_dominicana
    
    nombre = request.form.get('txt_nombre', '').strip()
    cedula = request.form.get('txt_cedula', '').strip()
    tarjeta = request.form.get('txt_tarjeta', '').strip()
    limite = request.form.get('txt_limite', '0').strip()
    tipo_persona = request.form.get('sel_tipo_persona', 'Física')
    estado = request.form.get('sel_estado', 'Activo')
    
    if not nombre or not cedula or not tarjeta or not limite:
        flash("Todos los campos obligatorios del cliente deben ser completados.", "warning")
        return redirect(url_for('clientes.listar_clientes'))
        
    if not validar_cedula_dominicana(cedula):
        flash(f"Error: La cédula '{cedula}' no es una cédula válida en República Dominicana.", "danger")
        return redirect(url_for('clientes.listar_clientes'))
        
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("SELECT id_cliente FROM clientes WHERE cedula = %s", (cedula,))
        if cursor.fetchone():
            cursor.close()
            flash(f"Error: La cédula '{cedula}' ya pertenece a un cliente registrado.", "danger")
            return redirect(url_for('clientes.listar_clientes'))
            
        cursor.execute("""
            INSERT INTO clientes (nombre, cedula, no_tarjeta_cr, limite_credito, tipo_persona, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, cedula, tarjeta, limite, tipo_persona, estado))
        mysql.connection.commit()
        cursor.close()
        flash(f"Cliente '{nombre}' registrado de manera exitosa.", "success")
    except Exception as e:
        flash(f"Error al guardar cliente: {str(e)}", "danger")
        
    return redirect(url_for('clientes.listar_clientes'))


@clientes_bp.route('/editar_cliente/<int:id_cliente>', methods=['POST'])
def editar_cliente(id_cliente):
    # 🟢 Importación local segura
    from app import mysql, validar_cedula_dominicana
    
    nombre = request.form.get('txt_nombre_edit', '').strip()
    cedula = request.form.get('txt_cedula_edit', '').strip()
    tarjeta = request.form.get('txt_tarjeta_edit', '').strip()
    limite = request.form.get('txt_limite_edit', '0').strip()
    tipo_persona = request.form.get('sel_tipo_persona_edit', 'Física')
    
    if not nombre or not cedula or not tarjeta or not limite:
        flash("Campos vacíos detectados al intentar actualizar.", "warning")
        return redirect(url_for('clientes.listar_clientes'))
        
    if not validar_cedula_dominicana(cedula):
        flash(f"Error: La cédula '{cedula}' no es una cédula válida.", "danger")
        return redirect(url_for('clientes.listar_clientes'))
        
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("SELECT id_cliente FROM clientes WHERE cedula = %s AND id_cliente != %s", (cedula, id_cliente))
        if cursor.fetchone():
            cursor.close()
            flash(f"Error: La cédula '{cedula}' ya está asignada a otro cliente.", "danger")
            return redirect(url_for('clientes.listar_clientes'))
            
        cursor.execute("""
            UPDATE clientes 
            SET nombre = %s, cedula = %s, no_tarjeta_cr = %s, limite_credito = %s, tipo_persona = %s 
            WHERE id_cliente = %s
        """, (nombre, cedula, tarjeta, limite, tipo_persona, id_cliente))
        mysql.connection.commit()
        cursor.close()
        flash("Datos de perfil del cliente actualizados correctamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar cliente: {str(e)}", "danger")
        
    return redirect(url_for('clientes.listar_clientes'))


@clientes_bp.route('/cambiar_estado_cliente/<int:id_cliente>/<string:nuevo_estado>')
def cambiar_estado_cliente(id_cliente, nuevo_estado):
    try:
        # 🟢 Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE clientes SET estado = %s WHERE id_cliente = %s", (nuevo_estado, id_cliente))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del cliente modificado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al alternar estado del cliente: {str(e)}", "danger")
        
    return redirect(url_for('clientes.listar_clientes'))
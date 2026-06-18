from flask import Blueprint, render_template, request, redirect, url_for, flash, session

#  Crea el Blueprint para Clientes 
clientes_bp = Blueprint('clientes', __name__)

#   Validación Oficial de RNC Dominicano (9 dígitos )
def validar_rnc_dominicano(rnc):
    """Valida estructuralmente un RNC de República Dominicana (9 dígitos, Módulo 11)"""
    if not rnc or not rnc.isdigit() or len(rnc) != 9:
        return False
        
    pesos = [7, 9, 8, 6, 5, 4, 3, 2]
    suma = 0
    
    for i in range(8):
        suma += int(rnc[i]) * pesos[i]
        
    division = suma % 11
    digito_verificador = 11 - division
    
    if digito_verificador == 11:
        digito_verificador = 2
    elif digito_verificador == 10:
        digito_verificador = 1
        
    return digito_verificador == int(rnc[8])


@clientes_bp.route('/clientes')
def listar_clientes():
    if 'usuario_id' not in session:
        flash("Acceso denegado. Por favor, inicie sesión.", "danger")
        return redirect(url_for('login'))
        
    try:
        # Importación local segura
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
    # Importación local segura
    from app import mysql, validar_cedula_dominicana
    
    nombre = request.form.get('txt_nombre', '').strip()
    #  Sanitiza guiones y espacios en blanco del formulario
    cedula_raw = request.form.get('txt_cedula', '').strip()
    cedula = cedula_raw.replace('-', '').replace(' ', '')
    
    tarjeta = request.form.get('txt_tarjeta', '').strip()
    limite_raw = request.form.get('txt_limite', '0').strip()
    tipo_persona = request.form.get('sel_tipo_persona', 'Física')
    estado = request.form.get('sel_estado', 'Activo')
    
    if not nombre or not cedula or not tarjeta or not limite_raw:
        flash("Todos los campos obligatorios del cliente deben ser completados.", "warning")
        return redirect(url_for('clientes.listar_clientes'))
        
    #   CANDADO DISCRIMINATORIO CONTEXTUAL (Física vs Jurídica)
    if tipo_persona == 'Física':
        if not validar_cedula_dominicana(cedula):
            flash(f" Error: La cédula '{cedula_raw}' no es válida ante la JCE para una Persona Física.", "danger")
            return redirect(url_for('clientes.listar_clientes'))
    elif tipo_persona == 'Jurídica':
        if not validar_rnc_dominicano(cedula):
            flash(f" Error: El RNC '{cedula_raw}' no es un RNC válido ante la DGII para una Persona Jurídica.", "danger")
            return redirect(url_for('clientes.listar_clientes'))
        
    try:
        limite = float(limite_raw)
        if limite < 0:
            limite = 0.0
    except ValueError:
        limite = 0.0
        
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("SELECT id_cliente FROM clientes WHERE cedula = %s", (cedula,))
        if cursor.fetchone():
            cursor.close()
            flash(f"Error: El documento de identidad '{cedula_raw}' ya pertenece a un cliente registrado.", "danger")
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
    # Importación local segura
    from app import mysql, validar_cedula_dominicana
    
    nombre = request.form.get('txt_nombre_edit', '').strip()
    #  Sanitiza guiones y espacios cargados desde la base de datos o el formulario
    cedula_raw = request.form.get('txt_cedula_edit', '').strip()
    cedula = cedula_raw.replace('-', '').replace(' ', '')
    
    tarjeta = request.form.get('txt_tarjeta_edit', '').strip()
    limite_raw = request.form.get('txt_limite_edit', '0').strip()
    tipo_persona = request.form.get('sel_tipo_persona_edit', 'Física')
    
    if not nombre or not cedula or not tarjeta or not limite_raw:
        flash("Campos vacíos detectados al intentar actualizar.", "warning")
        return redirect(url_for('clientes.listar_clientes'))
        
    #   CANDADO DISCRIMINATORIO CONTEXTUAL EN EDICIÓN:
    if tipo_persona == 'Física':
        if not validar_cedula_dominicana(cedula):
            flash(f" Error: La cédula '{cedula_raw}' no es válida ante la JCE.", "danger")
            return redirect(url_for('clientes.listar_clientes'))
    elif tipo_persona == 'Jurídica':
        if not validar_rnc_dominicano(cedula):
            flash(f" Error: El RNC '{cedula_raw}' no es un RNC válido ante la DGII.", "danger")
            return redirect(url_for('clientes.listar_clientes'))
        
    try:
        limite = float(limite_raw)
        if limite < 0:
            limite = 0.0
    except ValueError:
        limite = 0.0
        
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("SELECT id_cliente FROM clientes WHERE cedula = %s AND id_cliente != %s", (cedula, id_cliente))
        if cursor.fetchone():
            cursor.close()
            flash(f"Error: El documento '{cedula_raw}' ya está asignado a otro cliente.", "danger")
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
        # Importación local segura
        from app import mysql
        
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE clientes SET estado = %s WHERE id_cliente = %s", (nuevo_estado, id_cliente))
        mysql.connection.commit()
        cursor.close()
        flash(f"Estado del cliente modificado a '{nuevo_estado}' con éxito.", "success")
    except Exception as e:
        flash(f"Error al alternar estado del cliente: {str(e)}", "danger")
        
    return redirect(url_for('clientes.listar_clientes'))


# BORRADO FÍSICO SEGURO CON COMPROBACIÓN HISTÓRICA COMPLETA
@clientes_bp.route('/eliminar_cliente/<int:id_cliente>')
def eliminar_cliente(id_cliente):
    try:
        from app import mysql
        cursor = mysql.connection.cursor()
        
        # ESCANEO TOTAL: Buscamos si el cliente cuenta con rentas o inspecciones asentadas
        query_verificar = """
            SELECT 
                (SELECT COUNT(*) FROM rentas WHERE id_cliente = %s) AS en_rentas,
                (SELECT COUNT(*) FROM inspecciones WHERE id_cliente = %s) AS en_inspecciones
        """
        cursor.execute(query_verificar, (id_cliente, id_cliente))
        resultado = cursor.fetchone()
        
        ren = resultado['en_rentas'] if isinstance(resultado, dict) else resultado[0]
        insp = resultado['en_inspecciones'] if isinstance(resultado, dict) else resultado[1]
        
        if ren > 0 or insp > 0:
            cursor.close()
            flash("Operación denegada: No se puede eliminar este cliente permanentemente porque posee un historial de transacciones registrado (hojas de inspección o contratos de renta).", "danger")
            return redirect(url_for('clientes.listar_clientes'))
            
        cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
        mysql.connection.commit()
        cursor.close()
        
        flash("El registro del cliente ha sido removido físicamente del sistema de manera exitosa y segura.", "success")
    except Exception as e:
        flash(f"Error técnico de integridad al intentar eliminar al cliente: {str(e)}", "danger")
        
    return redirect(url_for('clientes.listar_clientes'))
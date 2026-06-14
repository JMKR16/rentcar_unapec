from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime

# 🔌 Blueprint para Rentas
rentas_bp = Blueprint('rentas', __name__)

@rentas_bp.route('/rentas')
def listar_rentas():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    try:
        from app import mysql
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT r.no_renta, CONCAT(v.no_placa, ' - ', m.descripcion, ' ', md.descripcion) AS vehiculo, 
                   c.nombre AS cliente, e.nombre AS empleado, r.fecha_renta, r.fecha_devolucion, 
                   r.monto_x_dia, r.cantidad_dias, r.monto_total, r.estado,
                   r.id_vehiculo, r.id_cliente, r.id_empleado, r.comentario, r.id_inspeccion
            FROM rentas r
            JOIN empleados e ON r.id_empleado = e.id_empleado
            JOIN vehiculos v ON r.id_vehiculo = v.id_vehiculo
            JOIN marcas m ON v.id_marca = m.id_marca
            JOIN modelos md ON v.id_modelo = md.id_modelo
            JOIN clientes c ON r.id_cliente = c.id_cliente
            ORDER BY r.no_renta DESC
        """
        cursor.execute(query)
        rentas = cursor.fetchall()

        query_inspecciones = """
            SELECT i.id_inspeccion, 
                   CONCAT('Insp #', i.id_inspeccion, ' - ', v.no_placa, ' (', c.nombre, ')') AS descripcion
            FROM inspecciones i
            JOIN vehiculos v ON i.id_vehiculo = v.id_vehiculo
            JOIN clientes c ON i.id_cliente = c.id_cliente
            WHERE i.estado = 'Activo'
              AND i.id_inspeccion NOT IN (SELECT id_inspeccion FROM rentas WHERE id_inspeccion IS NOT NULL)
              AND v.id_vehiculo NOT IN (SELECT id_vehiculo FROM rentas WHERE estado = 'Activo')
        """
        cursor.execute(query_inspecciones)
        inspecciones_disponibles = cursor.fetchall()
        
        cursor.close()

        return render_template('rentas.html', 
                               lista_rentas=rentas, 
                               lista_inspecciones=inspecciones_disponibles)
    except Exception as e:
        flash(f"Error al cargar el módulo de rentas: {str(e)}", "danger")
        return render_template('rentas.html', lista_rentas=[], lista_inspecciones=[])


@rentas_bp.route('/guardar_renta', methods=['POST'])
def guardar_renta():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    from app import mysql
    id_inspeccion = request.form.get('sel_inspeccion')
    fecha_renta_str = request.form.get('txt_fecha_renta')
    monto_x_dia = request.form.get('txt_monto_x_dia')
    comentario = request.form.get('txt_comentario', '').strip()

    if not id_inspeccion or not fecha_renta_str or not monto_x_dia:
        flash("Todos los campos obligatorios deben ser completados.", "warning")
        return redirect(url_for('rentas.listar_rentas'))

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("SELECT id_vehiculo, id_cliente, id_empleado_inspeccion FROM inspecciones WHERE id_inspeccion = %s", (id_inspeccion,))
        datos_insp = cursor.fetchone()

        if not datos_insp:
            flash("La inspección seleccionada no es válida.", "danger")
            cursor.close()
            return redirect(url_for('rentas.listar_rentas'))

        id_vehiculo = datos_insp['id_vehiculo'] if isinstance(datos_insp, dict) else datos_insp[0]
        id_cliente = datos_insp['id_cliente'] if isinstance(datos_insp, dict) else datos_insp[1]
        id_empleado = datos_insp['id_empleado_inspeccion'] if isinstance(datos_insp, dict) else datos_insp[2]

        # 🟢 Nace con fecha_devolucion en NULL/None porque todavía está en uso
        query = """
            INSERT INTO rentas (id_vehiculo, id_cliente, id_empleado, id_inspeccion, fecha_renta, fecha_devolucion, monto_x_dia, cantidad_dias, monto_total, estado, comentario)
            VALUES (%s, %s, %s, %s, %s, NULL, %s, 0, 0.00, 'Activo', %s)
        """
        cursor.execute(query, (id_vehiculo, id_cliente, id_empleado, id_inspeccion, fecha_renta_str, monto_x_dia, comentario))
        mysql.connection.commit()
        cursor.close()
        flash("Contrato de renta generado exitosamente. ¡Vehículo en uso!", "success")
    except Exception as e:
        flash(f"Error al procesar la salida del vehículo: {str(e)}", "danger")
        
    return redirect(url_for('rentas.listar_rentas'))


@rentas_bp.route('/editar_renta_activa', methods=['POST'])
def editar_renta_activa():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    from app import mysql
    no_renta = request.form.get('txt_no_renta')
    fecha_renta_str = request.form.get('txt_fecha_renta')
    monto_x_dia = request.form.get('txt_monto_x_dia')
    comentario = request.form.get('txt_comentario', '').strip()

    try:
        cursor = mysql.connection.cursor()
        # 🟢 Limpiamos el update quitando la fecha de devolución estipulada
        query = """
            UPDATE rentas 
            SET fecha_renta = %s, monto_x_dia = %s, comentario = %s
            WHERE no_renta = %s
        """
        cursor.execute(query, (fecha_renta_str, monto_x_dia, comentario, no_renta))
        mysql.connection.commit()
        cursor.close()
        flash("Contrato de renta corregido con éxito", "success")
    except Exception as e:
        flash(f"Error al modificar el contrato: {str(e)}", "danger")
        
    return redirect(url_for('rentas.listar_rentas'))


@rentas_bp.route('/marcar_devolucion', methods=['POST'])
def marcar_devolucion():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    from app import mysql
    no_renta = request.form.get('txt_no_renta')
    fecha_devolucion_str = request.form.get('txt_fecha_devolucion')

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT fecha_renta, monto_x_dia FROM rentas WHERE no_renta = %s", (no_renta,))
        renta = cursor.fetchone()

        if not renta:
            flash("No se encontró el registro de renta.", "danger")
            return redirect(url_for('rentas.listar_rentas'))

        f_renta_origen = renta['fecha_renta'] if isinstance(renta, dict) else renta[0]
        monto_diario = float(renta['monto_x_dia'] if isinstance(renta, dict) else renta[1])

        f_dev = datetime.strptime(fecha_devolucion_str, '%Y-%m-%d').date()
        if isinstance(f_renta_origen, str):
            f_renta = datetime.strptime(f_renta_origen, '%Y-%m-%d').date()
        elif isinstance(f_renta_origen, datetime):
            f_renta = f_renta_origen.date()
        else:
            f_renta = f_renta_origen

        # Doble validación en el Backend por seguridad:
        dias = (f_dev - f_renta).days
        if dias < 0:
            flash("Error: La fecha de devolución no puede ser menor a la fecha de inicio.", "danger")
            cursor.close()
            return redirect(url_for('rentas.listar_rentas'))
        elif dias == 0:
            dias = 1
            
        total_pesos = dias * monto_diario

        query_update = """
            UPDATE rentas 
            SET fecha_devolucion = %s, cantidad_dias = %s, monto_total = %s, estado = 'Devuelto'
            WHERE no_renta = %s
        """
        cursor.execute(query_update, (fecha_devolucion_str, dias, total_pesos, no_renta))
        mysql.connection.commit()
        cursor.close()
        
        flash(f"¡Vehículo recibido! Días calculados: {dias} | Monto Total: RD$ {total_pesos:,.2f}", "success")
    except Exception as e:
        flash(f"Error interno al procesar la devolución: {str(e)}", "danger")
        
    return redirect(url_for('rentas.listar_rentas'))
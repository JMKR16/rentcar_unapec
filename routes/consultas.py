from flask import Blueprint, render_template, request, session, redirect, url_for, flash, make_response
from datetime import datetime
import io

#  Blueprint  para Consultas Dinámicas
consultas_bp = Blueprint('consultas', __name__)

def generar_reporte_pdf(resultados):
    """Función auxiliar interna que fabrica el archivo PDF usando ReportLab"""
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1A1A1A"),
        spaceAfter=10
    )
    
    meta_style = ParagraphStyle(
        'ReportMeta',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#555555"),
        spaceAfter=20
    )
    
    story.append(Paragraph("RentCar - Reporte Ejecutivo de Rentas", title_style))
    fecha_impresion = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    story.append(Paragraph(f"Fecha de generación: {fecha_impresion} | Criterio: Reporte Filtrado de Operaciones", meta_style))
    story.append(Spacer(1, 10))
    
    # Encabezados de la tabla del PDF
    tabla_datos = [[
        "No. Renta", "Vehículo", "Cliente", "Asesor", 
        "F. Salida", "F. Entrada", "Tarifa/Día", "Días", "Monto Total", "Estado"
    ]]
    
    suma_total = 0.0
    for r in resultados:
        monto = float(r['monto_total']) if r['monto_total'] else 0.0
        suma_total += monto
        
        f_entrada = str(r['fecha_devolucion']) if r['fecha_devolucion'] else "En Uso"
        cant_dias = str(r['cantidad_dias']) if r['cantidad_dias'] else "0"
        
        tabla_datos.append([
            f"#{r['no_renta']}",
            r['vehiculo'],
            r['cliente'],
            r['empleado'],
            str(r['fecha_renta']),
            f_entrada,
            f"RD$ {r['monto_x_dia']:,.2f}",
            cant_dias,
            f"RD$ {monto:,.2f}",
            r['estado']
        ])
        
    tabla_datos.append([
        "TOTALES", "", "", "", "", "", "", "", f"RD$ {suma_total:,.2f}", f"{len(resultados)} Rentas"
    ])
    
    t = Table(tabla_datos, colWidths=[55, 120, 95, 80, 65, 65, 75, 35, 85, 55])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#212529")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D3D3")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#E9ECEF")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#1A1A1A")),
    ]))
    
    story.append(t)
    doc.build(story)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Reporte_Rentas_{datetime.now().strftime("%Y%m%d")}.pdf'
    return response


@consultas_bp.route('/consultas', methods=['GET', 'POST'])
def filtrar_rentas():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    try:
        from app import mysql
        cursor = mysql.connection.cursor()
        
        #  selector de vehículos
        cursor.execute("SELECT id_vehiculo, CONCAT(no_placa, ' - ', descripcion) AS descripcion FROM vehiculos")
        vehiculos_list = cursor.fetchall()
        
        #  Capturalos filtros por POST o GET de manera unificada
        filtro_vehiculo = request.values.get('sel_vehiculo', '')
        fecha_desde = request.values.get('txt_fecha_desde', '')
        fecha_hasta = request.values.get('txt_fecha_hasta', '')
        filtro_estado = request.values.get('sel_estado', '')
        
        #  Query base relacional de siempre
        query = """
            SELECT r.no_renta AS no_renta, 
                   CONCAT(v.no_placa, ' - ', m.descripcion, ' ', md.descripcion) AS vehiculo, 
                   c.nombre AS cliente, 
                   e.nombre AS empleado, 
                   r.fecha_renta AS fecha_renta, 
                   r.fecha_devolucion AS fecha_devolucion, 
                   r.monto_x_dia AS monto_x_dia, 
                   r.cantidad_dias AS cantidad_dias, 
                   r.monto_total AS monto_total, 
                   r.estado AS estado
            FROM rentas r
            JOIN empleados e ON r.id_empleado = e.id_empleado
            JOIN vehiculos v ON r.id_vehiculo = v.id_vehiculo
            JOIN marcas m ON v.id_marca = m.id_marca
            JOIN modelos md ON v.id_modelo = md.id_modelo
            JOIN clientes c ON r.id_cliente = c.id_cliente
            WHERE 1=1
        """
        params = []
        
        if filtro_vehiculo:
            query += " AND r.id_vehiculo = %s"
            params.append(filtro_vehiculo)
        if fecha_desde:
            query += " AND r.fecha_renta >= %s"
            params.append(fecha_desde)
        if fecha_hasta:
            query += " AND r.fecha_renta <= %s"
            params.append(fecha_hasta)
        if filtro_estado:
            query += " AND r.estado = %s"
            params.append(filtro_estado)
            
        query += " ORDER BY r.no_renta DESC"
        
        cursor.execute(query, tuple(params))
        resultados = cursor.fetchall()
        cursor.close()
        
        #  Si  Pulsa el botón de exportar PDF: 
        if request.method == 'POST' and request.form.get('btn_accion') == 'pdf':
            return generar_reporte_pdf(resultados)
            
        # Si no pulsó PDF (o entró por GET), procesa  la pantalla normal
        total_rentas_filtradas = len(resultados)
        suma_montos_acumulados = 0.0
        for r in resultados:
            if r['monto_total']:
                suma_montos_acumulados += float(r['monto_total'])
        
        return render_template('consultas.html', 
                               rentas=resultados, 
                               vehiculos=vehiculos_list, 
                               f_vehiculo=filtro_vehiculo,
                               f_desde=fecha_desde,
                               f_hasta=fecha_hasta,
                               f_estado=filtro_estado,
                               total_rentas=total_rentas_filtradas,
                               total_dinero=suma_montos_acumulados)
                               
    except Exception as e:
        flash(f"Error al procesar la consulta: {str(e)}", "danger")
        return render_template('consultas.html', rentas=[], vehiculos=[], total_rentas=0, total_dinero=0.0)
USE rentcar_unapec;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    clave VARCHAR(255) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo'
);

-- Se inserta un primer usuario administrador de pruebas
INSERT INTO usuarios (nombre, correo, clave, estado) 
VALUES ('Administrador', 'admin@rentcar.com', 'admin123', 'Activo')
ON DUPLICATE KEY UPDATE id_usuario=id_usuario;

select * from rentas;
select * from  clientes;
select * from  empleados;

TRUNCATE TABLE rentas;

--  Limpia cualquier intento previo fallido
TRUNCATE TABLE rentas;

-- Insertar con valor inicial 0 en los días y el monto total
INSERT INTO rentas (id_vehiculo, id_cliente, id_empleado, fecha_renta, fecha_devolucion, monto_x_dia, cantidad_dias, monto_total, estado, comentario)
VALUES (2, 2, 2, '2026-06-11', NULL, 1500.00, 0, 0.00, 'Activo', 'Prueba con datos reales del K5');


ALTER TABLE rentas ADD COLUMN monto_total DECIMAL(10,2) DEFAULT 0.00;
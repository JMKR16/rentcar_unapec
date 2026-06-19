
---Antes de hacer el primmer commit, olvide agregar el script INICIAL de la base de datos, 
---Este script simula mas o menos lo que utilice  para crear la base de datos desde cero, y también incluye algunos datos iniciales para pruebas. 
--- Sirve como una buena referencia para entender cómo se organizan las tablas y las relaciones entre ellas.
---Es importante destacar que este script es una representación aproximada   y puede no reflejar exactamente la estructura final de la base de datos
--- en el repositorio puse varios querys sueltos de las modificaciones que fui haciendo sobre la marcha, pero no el script completo de creación de la base de datos
---Así que aquí lo dejo para que quede registrado y se asemeje a  como  lo presenté el dia 18/06/2025 como parte del proyecto. 

CREATE DATABASE IF NOT EXISTS rentcar_unapec;
USE rentcar_unapec;

-- 1. TABLA: TIPOS DE VEHÍCULOS
CREATE TABLE IF NOT EXISTS tipos_vehiculos (
    id_tipo_vehiculo INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo'
);

-- 2. TABLA: MARCAS
CREATE TABLE IF NOT EXISTS marcas (
    id_marca INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo'
);

-- 3. TABLA: MODELOS
CREATE TABLE IF NOT EXISTS modelos (
    id_modelo INT AUTO_INCREMENT PRIMARY KEY,
    id_marca INT NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo',
    CONSTRAINT fk_modelos_marcas FOREIGN KEY (id_marca) REFERENCES marcas(id_marca)
);

-- 4. TABLA: TIPOS DE COMBUSTIBLE
CREATE TABLE IF NOT EXISTS tipos_combustible (
    id_tipo_combustible INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo'
);

-- 5. TABLA: VEHÍCULOS
CREATE TABLE IF NOT EXISTS vehiculos (
    id_vehiculo INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(200) NOT NULL,
    no_chasis VARCHAR(50) NOT NULL UNIQUE,
    no_motor VARCHAR(50) NOT NULL UNIQUE,
    no_placa VARCHAR(20) NOT NULL UNIQUE,
    id_tipo_vehiculo INT NOT NULL,
    id_marca INT NOT NULL,
    id_modelo INT NOT NULL,
    id_tipo_combustible INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo',
    CONSTRAINT fk_vehiculos_tipos FOREIGN KEY (id_tipo_vehiculo) REFERENCES tipos_vehiculos(id_tipo_vehiculo),
    CONSTRAINT fk_vehiculos_marcas FOREIGN KEY (id_marca) REFERENCES marcas(id_marca),
    CONSTRAINT fk_vehiculos_modelos FOREIGN KEY (id_modelo) REFERENCES modelos(id_modelo),
    CONSTRAINT fk_vehiculos_combustible FOREIGN KEY (id_tipo_combustible) REFERENCES tipos_combustible(id_tipo_combustible)
);

-- 6. TABLA: CLIENTES
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    cedula VARCHAR(20) NOT NULL UNIQUE,
    no_tarjeta_cr VARCHAR(30) NOT NULL,
    limite_credito DECIMAL(12,2) DEFAULT 0.00,
    tipo_persona VARCHAR(20) NOT NULL DEFAULT 'Física',
    estado VARCHAR(20) DEFAULT 'Activo'
);

-- 7. TABLA: EMPLEADOS
CREATE TABLE IF NOT EXISTS empleados (
    id_empleado INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    cedula VARCHAR(20) NOT NULL UNIQUE,
    tanda_laboral VARCHAR(50) NOT NULL,
    porcentaje_comision INT DEFAULT 0,
    fecha_ingreso DATE NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo'
);

-- 8. TABLA: USUARIOS (Estructura real: nombre y nombre_usuario)
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    clave VARCHAR(255) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo'
);

-- 9. TABLA: INSPECCIONES
CREATE TABLE IF NOT EXISTS inspecciones (
    id_inspeccion INT AUTO_INCREMENT PRIMARY KEY,
    id_vehiculo INT NOT NULL,
    id_cliente INT NOT NULL,
    id_empleado INT NOT NULL,
    fecha DATE NOT NULL,
    ralladuras VARCHAR(5) DEFAULT 'No',
    cant_combustible VARCHAR(50) NOT NULL,
    goma_repuesto VARCHAR(5) DEFAULT 'No',
    gato VARCHAR(5) DEFAULT 'No',
    roturas_cristal VARCHAR(5) DEFAULT 'No',
    estado_gomas VARCHAR(100) DEFAULT 'Buen Estado',
    estado VARCHAR(20) DEFAULT 'Activo',
    CONSTRAINT fk_inspecciones_vehiculo FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo),
    CONSTRAINT fk_inspecciones_cliente FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    CONSTRAINT fk_inspecciones_empleado FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado)
);

-- 10. TABLA: RENTAS Y DEVOLUCIONES
CREATE TABLE IF NOT EXISTS rentas (
    no_renta INT AUTO_INCREMENT PRIMARY KEY,
    id_inspeccion INT NOT NULL UNIQUE,
    id_vehiculo INT NOT NULL,
    id_cliente INT NOT NULL,
    id_empleado INT NOT NULL,
    fecha_renta DATE NOT NULL,
    fecha_devolucion DATE NULL,
    monto_x_dia DECIMAL(10,2) NOT NULL,
    cantidad_dias INT NULL,
    monto_total DECIMAL(12,2) NULL,
    comentario TEXT NULL,
    estado VARCHAR(20) DEFAULT 'Activo',
    CONSTRAINT fk_rentas_inspeccion FOREIGN KEY (id_inspeccion) REFERENCES inspecciones(id_inspeccion),
    CONSTRAINT fk_rentas_vehiculo FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo),
    CONSTRAINT fk_rentas_cliente FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    CONSTRAINT fk_rentas_empleado FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado)
);

-- ========================================================
-- INSERCIÓN DE DATOS BASE 
-- ========================================================

INSERT INTO usuarios (nombre, nombre_usuario, clave) 
VALUES ('Administrador', 'admin', 'admin123')
ON DUPLICATE KEY UPDATE nombre_usuario=nombre_usuario;

INSERT INTO tipos_combustible (descripcion) VALUES ('gasoil'), ('gasolina'), ('electrico'), ('glp');

INSERT INTO tipos_vehiculos (descripcion) VALUES ('Sedán'), ('Jeepeta'), ('Camioneta'), ('Compacto'), ('Camión'), ('Moto'), ('Coupe deportivo');